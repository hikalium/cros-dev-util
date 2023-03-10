#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# Copyright 2018 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Mock Omaha server"""

from __future__ import print_function

# pylint: disable=cros-logging-import
import argparse
import base64
import copy
import datetime
import errno
import json
import logging
import os
import shutil
import signal
import sys
import threading
import traceback

from xml.dom import minidom
from xml.etree import ElementTree

from six.moves import BaseHTTPServer
from six.moves import http_client
from six.moves import urllib


# '5' and '7' are just default values for testing.
_FIRMWARE_VER = '5'
_KERNEL_VER = '7'

# This is the same for all images on canary channel.
_CANARY_APP_ID = '{90F229CE-83E2-4FAF-8479-E368A34938B1}'


class Error(Exception):
  """The base class for failures raised by Nebraska."""


class InvalidRequestError(Error):
  """Raised for invalid requests."""


class Request(object):
  """Request consisting of a list of apps to update/install."""

  APP_TAG = 'app'
  APP_APPID_ATTR = 'appid'
  APP_DELTA_OKAY_ATTR = 'delta_okay'
  # The following app attributes should be the same for all incoming apps if
  # they exist. 'version' should be repeated in all apps, but other attributes
  # can be omited in non-platform apps. Or at least they should be present in
  # one of the apps. For this reason we keep these values in the Request
  # object itself and not the AppRequest (except for 'version').
  APP_VERSION_ATTR = 'version'
  APP_CHANNEL_ATTR = 'track'
  APP_BOARD_ATTR = 'board'

  UPDATE_CHECK_TAG = 'updatecheck'
  ROLLBACK_ALLOWED_ATTR = 'rollback_allowed'

  PING_TAG = 'ping'

  EVENT_TAG = 'event'
  EVENT_TYPE_ATTR = 'eventtype'
  EVENT_RESULT_ATTR = 'eventresult'
  EVENT_PREVIOUS_VERSION_ATTR = 'previousversion'

  # Update events and result codes.
  EVENT_TYPE_UNKNOWN = 0
  EVENT_TYPE_DOWNLOAD_COMPLETE = 1
  EVENT_TYPE_INSTALL_COMPLETE = 2
  EVENT_TYPE_UPDATE_COMPLETE = 3
  EVENT_TYPE_UPDATE_DOWNLOAD_STARTED = 13
  EVENT_TYPE_UPDATE_DOWNLOAD_FINISHED = 14

  EVENT_RESULT_ERROR = 0
  EVENT_RESULT_SUCCESS = 1
  EVENT_RESULT_SUCCESS_REBOOT = 2
  EVENT_RESULT_UPDATE_DEFERRED = 9

  # update_engine sends this version for all non-platform Apps when the
  # operation is install (or event for an install).
  _VERSION_ZERO = '0.0.0.0'

  class RequestType(object):
    """Simple enumeration for encoding request type."""
    INSTALL = 1 # Request installation of a new app.
    UPDATE = 2 # Request update for an existing app.
    EVENT = 3 # Just an event request.

  def __init__(self, request_str):
    """Initializes a request instance.

    Args:
      request_str: XML-formatted request string.
    """
    self.request_str = request_str
    logging.debug('Received request: %s', self.request_str)

    self.version = None
    self.track = None
    self.board = None
    self.request_type = None
    self.timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    self.app_requests = []

    self.ParseRequest()

  def ParseRequest(self):
    """Parse an XML request string into a list of app requests.

    An app request can be a no-op, an install request, or an update request, and
    may include a ping and/or event tag. We treat app requests with the update
    tag omitted as no-ops, since the server is not required to return payload
    information. Install requests are signalled by sending app requests along
    with a no-op request for the platform app.

    Returns:
      A list of AppRequest instances.

    Raises:
      InvalidRequestError if the request string is not a valid XML request.
    """
    try:
      request_root = ElementTree.fromstring(self.request_str)
    except ElementTree.ParseError as err:
      raise InvalidRequestError(
          'Request string is not valid XML: %s' % err)

    # TODO(http://crbug.com/914936): It would be better to specifically check
    # the platform app. An install is signalled by omitting the update_check for
    # the platform app, so we assume that if we have one appid for which the
    # update_check tag is omitted, it is the platform app and this is an install
    # request. This assumption should be fine since we never mix updates with
    # requests that do not include an update_check tag.
    app_elements = request_root.findall(self.APP_TAG)
    update_check_count = len(
        [x for x in app_elements if x.find(self.UPDATE_CHECK_TAG) is not None])
    if update_check_count == 0:
      self.request_type = Request.RequestType.EVENT
    elif update_check_count == len(app_elements) - 1:
      self.request_type = Request.RequestType.INSTALL
    elif update_check_count == len(app_elements):
      self.request_type = Request.RequestType.UPDATE
    else:
      raise InvalidRequestError(
          'Client request omits update_check tag for more than one, but not all'
          ' app requests.')

    for app in app_elements:
      app_request = Request.AppRequest(app, self.request_type)
      self.app_requests.append(app_request)

    def _CheckAttributesAndReturnIt(attribute, in_all=False, ignore_value=None):
      """Checks the attribute integrity among all apps and return its value.

      The most likely scenario is that the value of the attribute is the same
      for all apps if existed. It can optionally be in one or more apps, but
      they are all equal.

      Args:
        attribute: An attribute of the app tag.
        in_all: If true, the attribute should exist among all apps.
        ignore_value: The attribute value that we want to omit from the list of
          attributes.

      Returns:
        The value of the attribute. If no valid attribute value is found,
        ignore_value will be returned.
      """
      all_attrs = [getattr(x, attribute) for x in self.app_requests]
      if in_all and (ignore_value in all_attrs):
        raise InvalidRequestError(
            'All apps should have "%s" attribute.' % attribute)

      # Filter out non-ignore_value elements into a set.
      unique_attrs = set(x for x in all_attrs if x != ignore_value)
      if not unique_attrs:
        # If no app had the attribute, we can just return the invalid one as it
        # was the only one.
        return ignore_value

      if len(unique_attrs) > 1:
        raise InvalidRequestError(
            'Attribute "%s" is not the same in all app tags.' % attribute)
      return unique_attrs.pop()

    if self.request_type == Request.RequestType.UPDATE:
      # Update requests should have the same version for all Apps.
      self.version = _CheckAttributesAndReturnIt(self.APP_VERSION_ATTR,
                                                 in_all=True)
    else:
      # Install requests should have non-zero version for the platform App and
      # zero for all others. Event requests can be either for install or update
      # so they can have different combinations of versions.
      self.version = _CheckAttributesAndReturnIt(
          self.APP_VERSION_ATTR, ignore_value=self._VERSION_ZERO)

    self.track = _CheckAttributesAndReturnIt(self.APP_CHANNEL_ATTR)
    self.board = _CheckAttributesAndReturnIt(self.APP_BOARD_ATTR)
    if self.track is None or self.board is None:
      raise InvalidRequestError('Either track(%s) or board(%s) attributes are '
                                'empty in all apps.' % (self.track, self.board))

  def GetDict(self):
    """Returns a dictionary with some parameters of the request.

    This is mostly used by the auto update tests to capture the flow of requests
    from update_engine to analyze them (Simply in JSON format).
    """
    if not self.app_requests:
      return {}

    # TODO(ahassani): Extend this to return an object for all App Requests. For
    # now only can return the first one to be backward compatible with auto
    # update auto tests.
    result = self.app_requests[0].__dict__

    # Auto tests require an additional timestamp value which can be considered
    # as a Request wide varable and not App Request one. So set it here.
    result['timestamp'] = self.timestamp

    return result

  class AppRequest(object):
    """An app request.

    Can be an update request, install request, or neither if the update check
    tag is omitted (i.e. the platform app when installing a DLC, or when a
    request is only an event), in which case we treat the request as a no-op.
    An app request can also send pings and event result information.
    """

    def __init__(self, app, request_type):
      """Initializes a Request.

      Args:
        app: The request app XML element.
        request_type: install, update, or event.

        More on event pings:
        https://github.com/google/omaha/blob/master/doc/ServerProtocolV3.md
      """
      self.request_type = request_type
      self.appid = None
      self.version = None
      self.track = None
      self.board = None
      self.ping = None
      self.delta_okay = None
      self.event_type = None
      self.event_result = None
      self.previous_version = None
      self.rollback_allowed = None
      self.has_update_check = False

      self.ParseApp(app)

    def __str__(self):
      """Returns a string representation of an AppRequest."""
      if self.request_type == Request.RequestType.EVENT:
        return str(self.appid)
      elif self.request_type == Request.RequestType.INSTALL:
        return 'install %s v%s' % (self.appid, self.version)
      elif self.request_type == Request.RequestType.UPDATE:
        return '%s update %s from v%s' % (
            'delta' if self.delta_okay else 'full', self.appid, self.version)

    def ParseApp(self, app):
      """Parses the app XML element and populates the self object.

      Args:
        app: The request app XML element.

      Raises InvalidRequestError if the input request string is in
          invalid format.
      """
      self.appid = app.get(Request.APP_APPID_ATTR)
      self.version = app.get(Request.APP_VERSION_ATTR)
      self.track = app.get(Request.APP_CHANNEL_ATTR)
      self.board = app.get(Request.APP_BOARD_ATTR)
      self.delta_okay = app.get(Request.APP_DELTA_OKAY_ATTR) == 'true'

      update_check = app.find(Request.UPDATE_CHECK_TAG)
      self.has_update_check = update_check is not None
      self.rollback_allowed = (
          self.has_update_check and
          update_check.get(Request.ROLLBACK_ALLOWED_ATTR) == 'true')

      event = app.find(Request.EVENT_TAG)
      if event is not None:
        self.event_type = int(event.get(Request.EVENT_TYPE_ATTR))
        self.event_result = int(event.get(Request.EVENT_RESULT_ATTR, 0))
        self.previous_version = event.get(Request.EVENT_PREVIOUS_VERSION_ATTR)

      self.ping = app.find(Request.PING_TAG) is not None

      if None in (self.request_type, self.appid, self.version):
        raise InvalidRequestError('Invalid app request.')

    def MatchAppData(self, app_data, partial_match_appid=False,
                     check_against_canary=False, ignore_appid=False):
      """Returns true iff the app matches a given client request.

      An app matches a request if the appid matches the requested appid.
      Additionally, if the app describes a delta update payload, the request
      must be able to accept delta payloads.

      Args:
        app_data: An AppData object describing a valid app data.
        partial_match_appid: If true, it will partially check the app_data's
            appid.  Which means that if app_data's appid is a substring of
            request's appid, it will be a match.
        check_against_canary: If the DUT was on a canary channel, the App ID
            update_engine provides is from the canary channel, which is
            different from the release App ID that we use for generating payload
            properties file. But the good news is that there is only one canary
            App ID for all devices. Turning this flag on, checks the incoming
            request against the presumed canary App ID.
        ignore_appid: If true, don't check the App ID and assume a match.

      Returns:
        True if the request matches the given app, False otherwise.
      """
      if not ignore_appid and self.appid != app_data.appid:
        if partial_match_appid:
          if app_data.appid not in self.appid:
            return False
        elif check_against_canary:
          if app_data.canary_appid != self.appid:
            return False
        else:
          return False

      # At this point, there was a match.
      if self.request_type == Request.RequestType.UPDATE:
        if app_data.is_delta:
          return self.delta_okay
        else:
          return True

      if self.request_type == Request.RequestType.INSTALL:
        return not app_data.is_delta

      return False


class Response(object):
  """An update/install response.

  A response to an update or install request consists of an XML-encoded list
  of responses for each appid in the client request. This class takes a list of
  responses for update/install requests and compiles them into a single element
  constituting an aggregate response that can be returned to the client in XML
  format based on the format of an XML response template.
  """

  def __init__(self, request, nebraska_props, response_props):
    """Initialize a reponse from a list of matching apps.

    Args:
      request: Request instance describing client requests.
      nebraska_props: An instance of NebraskaProperties.
      response_props: An instance of ResponseProperties.
    """
    self._request = request
    self._nebraska_props = nebraska_props
    self._response_props = response_props

    curr = datetime.datetime.now()
    # Jan 1 2007 is the start of Omaha v3 epoch:
    # https://github.com/google/omaha/blob/master/doc/ServerProtocolV3.md#attributes-12
    self._elapsed_days = (curr - datetime.datetime(2007, 1, 1)).days
    self._elapsed_seconds = int((
        curr - datetime.datetime.combine(curr.date(),
                                         datetime.time.min)).total_seconds())

  def GetXMLString(self):
    """Generates a response to a set of client requests.

    Given a client request consisting of one or more app requests, generate a
    response to each of these requests and combine them into a single
    XML-formatted response.

    Returns:
      XML-formatted response string consisting of a response to each app request
      in the incoming request from the client.
    """
    try:
      response_xml = ElementTree.Element(
          'response', attrib={'protocol': '3.0', 'server': 'nebraska'})
      ElementTree.SubElement(
          response_xml, 'daystart',
          attrib={'elapsed_days': str(self._elapsed_days),
                  'elapsed_seconds': str(self._elapsed_seconds)})

      # The list of app data that we have already matched. This is populated
      # during the for loop below.
      matched_apps = set()
      for app_request in self._request.app_requests:
        response_xml.append(
            self.AppResponse(app_request, self._nebraska_props,
                             self._response_props, matched_apps).Compile())

    except Exception as err:
      logging.error(traceback.format_exc())
      raise Error('Failed to compile response: %s' % err)

    return ElementTree.tostring(
        response_xml, encoding='UTF-8', method='xml')

  class AppResponse(object):
    """Response to an app request.

    If the request was an update or install request, the response should include
    a matching app if one was found. Addionally, the response should include
    responses to pings and events as appropriate.
    """

    def __init__(self, app_request, nebraska_props, response_props,
                 matched_apps):
      """Initialize an AppResponse.

      Args:
        app_request: AppRequest representing a client request.
        nebraska_props: An instance of NebraskaProperties.
        response_props: An instance of ResponseProperties.
        matched_apps: The set of app data that have been matched already.
      """
      self._app_request = app_request
      self._response_props = response_props
      self._app_data = None
      self._payloads_address = None
      # Although, for installs the update_engine probably should not care about
      # critical updates and should install even if OOBE has not been passed.
      self._critical_update = self._response_props.critical_update

      # If no update was requested, don't process anything anymore.
      if self._response_props.no_update:
        return

      if self._app_request.request_type == Request.RequestType.INSTALL:
        # Platform requests for install should not have any payload associated
        # with them.
        if self._app_request.has_update_check:
          self._app_data = nebraska_props.install_app_index.Find(
              self._app_request, matched_apps, True)
        self._payloads_address = nebraska_props.install_payloads_address

      elif self._app_request.request_type == Request.RequestType.UPDATE:
        self._app_data = nebraska_props.update_app_index.Find(
            self._app_request, matched_apps, self._response_props.full_payload,
            nebraska_props.ignore_appid)
        self._payloads_address = nebraska_props.update_payloads_address

      if self._app_data:
        logging.debug('Found matching payload: %s', str(self._app_data))
      elif self._app_request.request_type == Request.RequestType.UPDATE:
        logging.debug('No matching updates payload available for App ID %s',
                      self._app_request.appid)
      elif (self._app_request.has_update_check and
            self._app_request.request_type == Request.RequestType.INSTALL):
        logging.debug('No matching install payload available for App ID %s',
                      self._app_request.appid)

    def Compile(self):
      """Compiles an app description into XML format.

      Compile the app description into an ElementTree Element that can be used
      to compile a response to a client request, and ultimately converted into
      XML.

      Returns:
        An ElementTree Element instance describing an update or install payload.
      """
      app_response = ElementTree.Element(
          'app', attrib={'appid': self._app_request.appid, 'status': 'ok'})

      if self._app_request.ping:
        ElementTree.SubElement(app_response, 'ping', attrib={'status': 'ok'})
      if self._app_request.event_type is not None:
        ElementTree.SubElement(app_response, 'event', attrib={'status': 'ok'})

      if self._app_data is not None:
        update_check_attribs = {'status': 'ok'}
        if (self._response_props.is_rollback and
            self._app_request.rollback_allowed):
          update_check_attribs['_is_rollback'] = 'true'
          # Techincally we have to always send _firmware_version and
          # _kernel_version attributes regardless of the rollback situation. But
          # for the sake of simplicity, we can just send it when rollback was
          # requested.
          index_strs = ['', '_0', '_1', '_2', '_3', '_4']
          for idx in index_strs:
            update_check_attribs['_firmware_version' + idx] = _FIRMWARE_VER
            update_check_attribs['_kernel_version' + idx] = _KERNEL_VER
        if self._response_props.eol_date is not None:
          update_check_attribs['_eol_date'] = str(self._response_props.eol_date)
        update_check = ElementTree.SubElement(
            app_response, 'updatecheck', attrib=update_check_attribs)
        urls = ElementTree.SubElement(update_check, 'urls')
        for _ in range(self._response_props.num_urls):
          ElementTree.SubElement(
              urls, 'url', attrib={'codebase': self._payloads_address})
        manifest = ElementTree.SubElement(
            update_check, 'manifest',
            attrib={'version': self._app_data.target_version})
        actions = ElementTree.SubElement(manifest, 'actions')
        ElementTree.SubElement(
            actions, 'action',
            attrib={'event': 'update', 'run': self._app_data.name})
        action = ElementTree.SubElement(
            actions, 'action',
            attrib={'ChromeOSVersion': self._app_data.target_version,
                    'ChromeVersion': '1.0.0.0',
                    'DisablePayloadBackoff': str(
                        self._response_props.disable_payload_backoff).lower(),
                    'IsDeltaPayload': str(self._app_data.is_delta).lower(),
                    'MaxDaysToScatter': '14',
                    'MetadataSignatureRsa': self._app_data.metadata_signature,
                    'MetadataSize': str(self._app_data.metadata_size),
                    'sha256': self._app_data.sha256,
                    'event': 'postinstall'})
        if self._response_props.failures_per_url is not None:
          action.set('MaxFailureCountPerUrl',
                     str(self._response_props.failures_per_url))
        if self._critical_update:
          action.set('deadline', 'now')
        if self._app_data.public_key is not None:
          action.set('PublicKeyRsa', self._app_data.public_key)
        packages = ElementTree.SubElement(manifest, 'packages')
        ElementTree.SubElement(
            packages, 'package',
            attrib={'fp': '1.%s' % self._app_data.sha256_hex,
                    'hash_sha256': self._app_data.sha256_hex,
                    'name': self._app_data.name,
                    'required': 'true',
                    'size': str(self._app_data.size)})

      # For installs, if there was no updatecheck, there will be no updatecheck
      # response. Just a no update in the app tag's status attribute.
      elif (self._app_request.request_type == Request.RequestType.INSTALL and
            not self._app_request.has_update_check):
        app_response.attrib['status'] = 'noupdate'
      elif self._app_request.request_type == Request.RequestType.UPDATE:
        update_check_attribs = {'status': 'noupdate'}
        if self._response_props.eol_date is not None:
          update_check_attribs['_eol_date'] = str(self._response_props.eol_date)
        ElementTree.SubElement(app_response, 'updatecheck',
                               attrib=update_check_attribs)

      return app_response


class AppIndex(object):
  """An index of available app payload information.

  Index of available apps used to generate responses to Omaha requests. The
  index consists of lists of payload information associated with a given appid,
  since we can have multiple payloads for a given app (delta/full payloads). The
  index is built by scanning a given directory for json files that describe the
  available payloads.

  Attributes:
    _directory: Directory containing metdata and payloads, can be None.
    _index: A list of AppData describing payloads.
  """

  def __init__(self, directory):
    """Initializes an AppIndex instance."""
    self._directory = directory
    self._index = []

    self._Scan()

  def _Scan(self):
    """Scans the directory and loads all available properties files."""
    if self._directory is None:
      return

    for f in os.listdir(self._directory):
      if f.endswith('.json'):
        try:
          with open(os.path.join(self._directory, f), 'r') as metafile:
            metadata_str = metafile.read()
            metadata = json.loads(metadata_str)
            # Get the name from file name itself, assuming the metadata file
            # ends with '.json'.
            metadata[AppIndex.AppData.NAME_KEY] = f[:-len('.json')]
            app = AppIndex.AppData(metadata)
            self._index.append(app)
        except (IOError, KeyError, ValueError) as err:
          logging.error('Failed to read app data from %s (%s)', f, str(err))
          raise
        logging.debug('Found app data: %s', str(app))

  def Find(self, request, matched_apps, full_payload, ignore_appid=False):
    """Search the index for a given appid.

    Searches the index for the payloads matching a client request. Matching is
    based on appid, and whether the client is searching for an update and can
    handle delta payloads.

    Args:
      request: AppRequest describing the client request.
      matched_apps: The set of app data that have been matched already.
      full_payload: True if we want full payload, False if delta payload, None
        if we don't care.
      ignore_appid: True to ignore the request's App ID and use the first
        available app.

    Returns:
      An AppData object describing an available payload matching the client
      request, or None if no matches are found. Prefer delta payloads if the
      client can accept them and if one is available.
    """
    # Find a list of payloads exactly matching the client request.
    matches = [app_data for app_data in self._index if
               request.MatchAppData(app_data)]

    # Check to see if the incoming requests where from a canary channel (mostly
    # a test image).
    if not matches:
      matches = [app_data for app_data in self._index if
                 request.MatchAppData(app_data, check_against_canary=True)]

    if not matches:
      # Look to see if there is any AppData with empty or partial App ID. Then
      # return the first one you find. This basically will work as a wild card
      # to allow AppDatas that don't have an AppID or their AppID is incomplete
      # (e.g. empty platform App ID + _ + DLC App ID) to work just fine.
      #
      # The reason we just don't do this in one pass is that we want to find all
      # the matches with exact appid and iif there was no match, we do the appid
      # partial match.
      matches = [app_data for app_data in self._index if
                 request.MatchAppData(app_data, partial_match_appid=True)]

    if not matches and ignore_appid:
      matches = [app_data for app_data in self._index if
                 request.MatchAppData(app_data, ignore_appid=True)]

    # Now remove App ID matches that have already been matched by other
    # requests.
    matches = [app_data for app_data in matches
               if app_data not in matched_apps]

    if full_payload is False and not request.delta_okay:
      logging.error('The update client indicated that it can not accept a delta'
                    ' payload, but the Nebraska is instructed to only serve'
                    ' delta payload. This is a bug.')
      return None

    full_match = next((x for x in matches if not x.is_delta), None)
    delta_match = next((x for x in matches if x.is_delta), None)

    if full_payload or not request.delta_okay:
      match = full_match
    else:
      match = (delta_match if full_payload is False or delta_match
               else full_match)

    if not match:
      return None

    # Add this App data to the list of already matched ones.
    matched_apps.add(match)

    return copy.copy(match)

  class AppData(object):
    """Data about an available app.

    Data about an available app that can be either installed or upgraded
    to. This information is compiled into XML format and returned to the client
    in an app tag in the server's response to an update or install request.

    Attributes:
      appid: App ID of the requested app.
      canary_appid: canary version App ID of the requested app.
      name: Filename of requested app on the mock Lorry server.
      is_delta: True iff the payload is a delta update.
      size: Size of the payload.
      metadata_signature: Metadata signature.
      metadata_size: Metadata size.
      sha256_hex: SHA256 hash of the payload encoded in hexadecimal.
      sha256: SHA256 hash of the payload encoded in base64 format.
      target_version: ChromeOS version the payload is tied to.
      source_version: Source version for delta updates.
      public_key: The public key for signature verification. It should be in
          base64 format.
    """
    APPID_KEY = 'appid'
    NAME_KEY = 'name'
    IS_DELTA_KEY = 'is_delta'
    SIZE_KEY = 'size'
    METADATA_SIG_KEY = 'metadata_signature'
    METADATA_SIZE_KEY = 'metadata_size'
    TARGET_VERSION_KEY = 'target_version'
    SOURCE_VERSION_KEY = 'source_version'
    SHA256_HEX_KEY = 'sha256_hex'
    PUBLIC_KEY_RSA_KEY = 'public_key'

    def __init__(self, app_data):
      """Initialize AppData.

      Args:
        app_data: Dictionary containing attributes used to initialize AppData
            instance.
      """
      self.appid = app_data[self.APPID_KEY]
      # Replace the begining of the App ID with the canary version.
      self.canary_appid = ''
      if len(self.appid) >= len(_CANARY_APP_ID):
        self.canary_appid = (_CANARY_APP_ID +
                             self.appid[len(_CANARY_APP_ID):])
      self.name = app_data[self.NAME_KEY]
      self.target_version = app_data[self.TARGET_VERSION_KEY]
      self.is_delta = app_data[self.IS_DELTA_KEY]
      self.source_version = (
          app_data[self.SOURCE_VERSION_KEY] if self.is_delta else None)
      self.size = app_data[self.SIZE_KEY]
      # Sometimes the payload is not signed, hence the matadata signature is
      # null, but we should pass empty string instead of letting the value be
      # null (the XML element tree will break).
      self.metadata_signature = app_data[self.METADATA_SIG_KEY] or ''
      self.metadata_size = app_data[self.METADATA_SIZE_KEY]
      self.public_key = app_data.get(self.PUBLIC_KEY_RSA_KEY)
      # Unfortunately the sha256_hex that paygen generates is actually a base64
      # sha256 hash of the payload for some unknown historical reason. But the
      # Omaha response contains the hex value of that hash. So here convert the
      # value from base64 to hex so nebraska can send the correct version to the
      # client. See b/131762584.
      self.sha256 = app_data[self.SHA256_HEX_KEY]
      self.sha256_hex = base64.b16encode(
          base64.b64decode(self.sha256)).decode('utf-8')
      self.url = None # Determined per-request.

    def __str__(self):
      if self.is_delta:
        return '%s v%s: delta update from base v%s' % (
            self.appid, self.target_version, self.source_version)
      return '%s v%s: full update/install' % (
          self.appid, self.target_version)


class NebraskaProperties(object):
  """An instance of this class contains Nebraska properties.

  These properties are valid and unchanged during the lifetime of the nebraska.
  """

  def __init__(self,
               update_payloads_address=None,
               install_payloads_address=None,
               update_metadata_dir=None,
               install_metadata_dir=None,
               ignore_appid=False):
    """Initializes the NebraskaProperties instance.

    Args:
      update_payloads_address: Address of the update payload server.
      install_payloads_address: Address of the install payload server. If None
           is passed it will default to update_payloads_address.
      update_metadata_dir: Update payloads metadata directory.
      install_metadata_dir: Install payloads metadata directory.
      ignore_appid: True to ignore the request's App ID and use the first
        available app.
    """
    # Attach '/' at the end of the addresses if they don't have any. The update
    # engine just concatenates the base address with the payload file name and
    # if there is no '/' the path will be invalid.
    self.update_payloads_address = os.path.join(update_payloads_address or '',
                                                '')
    self.install_payloads_address = (
        os.path.join(install_payloads_address or '', '') or
        self.update_payloads_address)
    self.update_app_index = AppIndex(update_metadata_dir)
    self.install_app_index = AppIndex(install_metadata_dir)
    self.ignore_appid = ignore_appid


class ResponseProperties(object):
  """An instance of this class contains properties applied for each response.

  These properties might change during the lifetime of the nebraska.
  """
  def __init__(self, **kwargs):
    """Initliazes the response properties.

    Args:
      kwargs: A dictionary of key values to initialize the response
        properties. A list of acceptable values are defined below. Any key other
        than the list below is simply ignored. The reason for this is that
        sometimes the client sends extra values that are only valuable to the
        devserver, but not to Nebraska. That way devserver can just pass through
        the args to Nebraska without picking the valuable ones.

        - critical_update: If true, the response will include 'deadline=now'
          which indicates the update is critical.
        - no_update: If true, it will return a noupdate response regardless.
        - is_rollback: Whether the update request will be a rollback or not.
        - failures_per_url: How many times each url can fail.
        - disable_payload_backoff: Instruct update_engine to disable the
          back-off logic on the client altogether.
        - num_urls: Number of URLs that should be returned in the response.
        - eol_date: The number of days from unix epoch which device goes end of
          life.
        - full_payload: Indicates whether we want a full payload or not. None
          means we don't care.
    """
    self.critical_update = kwargs.get('critical_update', False)
    self.no_update = kwargs.get('no_update', False)
    self.is_rollback = kwargs.get('is_rollback', False)
    self.failures_per_url = kwargs.get('failures_per_url', None)
    self.disable_payload_backoff = kwargs.get('disable_payload_backoff', False)
    self.num_urls = kwargs.get('num_urls', 1)
    self.eol_date = kwargs.get('eol_date', None)
    self.full_payload = kwargs.get('full_payload', None)


class Nebraska(object):
  """An instance of this class allows responding to incoming Omaha requests.

    This class has the responsibility to manufacture Omaha responses based on
    the input update requests. This should be the main point of use of the
    Nebraska. If any changes to the behavior of Nebraska is intended, like
    creating critical update responses, or messing up with firmware and kernel
    versions, new flags should be added here to add that feature.
  """
  def __init__(self, nebraska_props=None, response_props=None):
    """Initializes the Nebraska instance.

    Args:
      nebraska_props: An instance of NebraskaProperties.
      response_props: An instance of ResponseProperties.
    """
    self._nebraska_props = nebraska_props or NebraskaProperties()
    self._response_props = response_props or ResponseProperties()
    self._request_log = []

  def GetResponseToRequest(self, request, response_props=None):
    """Returns the response corresponding to a request.

    Args:
      request: The Request object representation of the incoming request.
      response_props: An instance of ResponseProperties. If passed, it will
        override the internal Nebraska version (default).

    Returns:
      The string representation of the created response.
    """
    self._request_log.append(request.GetDict())

    response = Response(request, self._nebraska_props,
                        response_props or self._response_props).GetXMLString()
    # Make the XML response look pretty.
    response_str = minidom.parseString(response).toprettyxml(indent='  ',
                                                             encoding='UTF-8')
    logging.debug('Sent response: %s', response_str)
    return response_str

  def GetRequestLog(self):
    """Returns the request logs in JSON format."""
    return json.dumps(self._request_log).encode('utf-8')


def QueryDictToDict(query):
  """Converts the query string generated dict to a proper one.

  This function gets a dictionary that was generated by parsing functions in
  cherrypy or urllib and converts it into a dictionary that is has values in
  proper format like True (as boolean) instead of 'True' (as string). It also
  only converts values that nebraska knows about. It ignores other ones.
  e.g:
    {'foo': 'bar', 'test': 'True', 'cros': '12', 'hello': ['world', 'lord']} ->
    {'foo': 'bar', 'test': True, 'cros': 12, 'hello': 'world'}

  Args:
    query: A dictionary of key values. The values can either be a string or a
      list. If the value is a list, only the first element of the list is used.

  Returns:
    The converted dictionary.
  """
  true_lambda = lambda a: a == 'True'
  kwargs = {}
  for k, t in {
      'critical_update': true_lambda,
      'disable_payload_backoff':  true_lambda,
      'eol_date': int,
      'failures_per_url': int,
      'no_update': true_lambda,
      'num_urls': int,
      'full_payload': true_lambda,
  }.items():
    value = query.get(k)
    if value:
      kwargs[k] = t(value[0] if isinstance(value, list) else value)
  return kwargs

class NebraskaServer(object):
  """A simple Omaha server instance.

  A simple mock of an Omaha server. Responds to XML-formatted update/install
  requests based on the contents of metadata files in update and install
  directories, respectively. These metadata files are used to configure
  responses to Omaha requests from Update Engine and describe update and install
  payloads provided by another server.
  """

  def __init__(self, nebraska, runtime_root=None, port=0):
    """Initializes a server instance.

    Args:
      nebraska: The Nebraska instance to process requests and responses.
      runtime_root: The root directory in which nebraska will write its PID and
        port files.
      port: Port the server should run on, 0 if the OS should assign a port.
    """
    self.nebraska = nebraska
    self._runtime_root = runtime_root
    self._port = port

    if self._runtime_root:
      self._port_file = os.path.join(self._runtime_root, 'port')
      self._pid_file = os.path.join(self._runtime_root, 'pid')

    self._httpd = None
    self._server_thread = None
    self._created_runtime_root = False

  class NebraskaHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    """HTTP request handler for Omaha requests."""

    def _SendResponse(self, content_type, response, code=http_client.OK):
      """Sends a given response back to the client.

      Args:
        content_type: The content type of the response data: xml, json, etc.
        response: The response content in string format.
        code: The HTTP code to send back to the client.
      """
      self.send_response(code)
      self.send_header('Content-Type', content_type)
      self.end_headers()
      self.wfile.write(response)

    def _ParseURL(self, url):
      """Parses a URL into usable components.

      Args:
        url: The input URL to parse.

      Returns:
        A tuple of parsed path and parsed query. The parsed query is a
        dictionary of keys to list of values. e.g:
        - http://goo.gle/path/?key=value1&key=value2 ->
          ('path', {'key': ['value1', 'value2']})
      """
      parsed_result = urllib.parse.urlparse(url)
      parsed_path = parsed_result.path.strip('/')
      parsed_query = urllib.parse.parse_qs(parsed_result.query)
      return parsed_path, parsed_query

    def do_POST(self):
      """Responds to XML-formatted Omaha requests.

      The URL path can be like:
          https://<ip>:<port>/update/?key1=value1&key2=value2...

      Look at ResponseProperties for a list of available attributes.
      """
      try:
        request_len = int(self.headers.get('content-length'))
        request = self.rfile.read(request_len)
      except Exception as err:
        logging.error('Failed to read request in do_POST %s', str(err))
        self.send_error(http_client.BAD_REQUEST, 'Invalid request (header).')
        return

      parsed_path, parsed_query = self._ParseURL(self.path)
      if parsed_path == 'update':
        kwargs = QueryDictToDict(parsed_query)
        response_props = ResponseProperties(**kwargs)

        try:
          request_obj = Request(request)
          response = self.server.owner.nebraska.GetResponseToRequest(
              request_obj, response_props)
          self._SendResponse('application/xml', response)
        except Exception as err:
          logging.error('Failed to handle request (%s)', str(err))
          logging.error(traceback.format_exc())
          self.send_error(http_client.INTERNAL_SERVER_ERROR,
                          traceback.format_exc())

      else:
        logging.error('The requested path "%s" was not found!', parsed_path)
        self.send_error(http_client.BAD_REQUEST,
                        'The requested path "%s" was not found!' % parsed_path)

    def do_GET(self):
      """Responds to Get requests.

      The use cases are:
      - requestlog: For getting the list of request logs in a JSON format.

      The URL path can be like:
          https://<ip>:<port>/requestlog
      """
      parsed_path, _ = self._ParseURL(self.path)

      if parsed_path == 'requestlog':
        try:
          response = self.server.owner.nebraska.GetRequestLog()
          self._SendResponse('application/json', response)
        except Exception as err:
          logging.error('Failed to get request logs (%s)', str(err))
          logging.error(traceback.format_exc())
          self.send_error(http_client.INTERNAL_SERVER_ERROR,
                          traceback.format_exc())
      elif parsed_path == 'health_check':
        self._SendResponse('text/plain', 'Nebraska is alive!')
      else:
        logging.error('The requested path "%s" was not found!', parsed_path)
        self.send_error(http_client.BAD_REQUEST,
                        'The requested path "%s" was not found!' % parsed_path)

  def Start(self):
    """Starts the nebraska server."""
    self._httpd = BaseHTTPServer.HTTPServer(('', self.GetPort()),
                                            NebraskaServer.NebraskaHandler)
    self._port = self._httpd.server_port

    if self._runtime_root:
      try:
        if not os.path.exists(self._runtime_root):
          os.makedirs(self._runtime_root)
          self._created_runtime_root = True
        with open(self._port_file, 'w') as port_file:
          port_file.write(str(self._port))
        with open(self._pid_file, 'w') as pid_file:
          pid_file.write(str(os.getpid()))
      except IOError as err:
        if err.errno == errno.EACCES:
          print('Permission error: You need to run the script as root/sudo or '
                'change the --runtime-root to point to a non-root accessible '
                'location.')
        raise

    self._httpd.owner = self
    self._server_thread = threading.Thread(target=self._httpd.serve_forever)
    self._server_thread.start()

    logging.info('Started nebraska on port %d and pid %d.',
                 self._port, os.getpid())

  def Stop(self):
    """Stops the mock Omaha server."""
    self._httpd.shutdown()
    self._server_thread.join()

    if not self._runtime_root:
      return
    for f in {self._port_file, self._pid_file}:
      try:
        os.remove(f)
      except Exception as e:
        logging.warning('Failed to remove file %s with error %s', f, e)
    if self._created_runtime_root:
      try:
        shutil.rmtree(self._runtime_root)
      except Exception as e:
        logging.warning('Failed to remove directory %s with error %s',
                        self._runtime_root, e)


  def GetPort(self):
    """Returns the server's port."""
    return self._port


def ParseArguments(argv):
  """Parses command line arguments.

  Args:
    argv: List of commandline arguments.

  Returns:
    Namespace object containing parsed arguments.
  """
  parser = argparse.ArgumentParser(
      description=__doc__,
      formatter_class=argparse.ArgumentDefaultsHelpFormatter)

  parser.add_argument('--update-metadata', metavar='DIR', default=None,
                      help='Payloads metadata directory for update.')
  parser.add_argument('--install-metadata', metavar='DIR', default=None,
                      help='Payloads metadata directory for install.')
  parser.add_argument('--update-payloads-address', metavar='URL',
                      help='Base payload URI for update payloads',
                      default='http://127.0.0.1:8080')
  parser.add_argument('--install-payloads-address', metavar='URL',
                      help='Base payload URI for install payloads. If not '
                      'passed it will default to --update-payloads-address')
  parser.add_argument('--ignore-appid', action='store_true',
                      help='Ignore the App ID field of incoming requests and '
                      'use whichever app is available.')

  parser.add_argument('--port', metavar='PORT', type=int, default=0,
                      help='Port to run the server on.')
  parser.add_argument('--runtime-root', metavar='DIR',
                      default='/run/nebraska',
                      help='The root directory in which nebraska will write its'
                      ' pid and port files.')
  parser.add_argument('--log-file', metavar='FILE', default='/tmp/nebraska.log',
                      help='The file to write the logs.'
                      ' pass "stdout" to write to standard output.')

  return parser.parse_args(argv[1:])


def main(argv):
  """Main function."""
  opts = ParseArguments(argv)

  # Reset the log file.
  if opts.log_file != 'stdout':
    with open(opts.log_file, 'w') as _:
      pass
    print('Logging to %s' % opts.log_file)

  logging.basicConfig(filename=(opts.log_file if opts.log_file != 'stdout'
                                else None),
                      level=logging.DEBUG)

  logging.info('Starting nebraska ...')

  nebraska_props = NebraskaProperties(
      update_payloads_address=opts.update_payloads_address,
      install_payloads_address=opts.install_payloads_address,
      update_metadata_dir=opts.update_metadata,
      install_metadata_dir=opts.install_metadata,
      ignore_appid=opts.ignore_appid)
  nebraska = Nebraska(nebraska_props)
  nebraska_server = NebraskaServer(nebraska, runtime_root=opts.runtime_root,
                                   port=opts.port)

  def handler(signum, _):
    logging.info('Exiting Nebraska with signal %d ...', signum)
    nebraska_server.Stop()

  signal.signal(signal.SIGINT, handler)
  signal.signal(signal.SIGTERM, handler)

  nebraska_server.Start()

  signal.pause()

  return os.EX_OK


if __name__ == '__main__':
  sys.exit(main(sys.argv))
