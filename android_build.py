# Copyright 2015 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Helper methods to make Google API call to query Android build server."""

from __future__ import print_function

import apiclient
import httplib2
import io
import subprocess

from apiclient import discovery
from oauth2client.client import SignedJwtAssertionCredentials

import retry


CREDENTIAL_SCOPE = 'https://www.googleapis.com/auth/androidbuild.internal'
DEFAULT_BUILDER = 'androidbuildinternal'
DEFAULT_CHUNKSIZE = 20*1024*1024
# Maximum attempts to interact with Launch Control API.
MAX_ATTEMPTS = 10
# Timeout in minutes for downloading attempt.
DOWNLOAD_TIMEOUT_MINS = 30
# Timeout in minutes for API query.
QUERY_TIMEOUT_MINS = 1


class AndroidBuildFetchError(Exception):
  """Exception to raise when failed to make calls to Android build server."""

class BuildAccessor(object):
  """Wrapper class to make Google API call to query Android build server."""

  # Credential information is required to access Android builds. The values will
  # be set when the devserver starts.
  credential_info = None

  @classmethod
  @retry.retry(Exception, timeout_min=QUERY_TIMEOUT_MINS)
  def _GetServiceObject(cls):
    """Returns a service object with given credential information."""
    if not cls.credential_info:
      raise AndroidBuildFetchError('Android Build credential is missing.')

    credentials = SignedJwtAssertionCredentials(
        cls.credential_info['client_email'],
        cls.credential_info['private_key'], CREDENTIAL_SCOPE)
    http_auth = credentials.authorize(httplib2.Http())
    return discovery.build(DEFAULT_BUILDER, 'v1', http=http_auth)


  @classmethod
  def _VerifyBranch(cls, service_obj, branch, build_id, target):
    """Verify the build with given id and target is for the specified branch.

    Args:
      service_obj: A service object to be used to make API call to build server.
      branch: branch of the desired build.
      build_id: Build id of the Android build, e.g., 2155602.
      target: Target of the Android build, e.g., shamu-userdebug.

    Raises:
      AndroidBuildFetchError: If the given build id and target are not for the
                              specified branch.
    """
    builds = service_obj.build().list(
        buildType='submitted', branch=branch, buildId=build_id, target=target,
        maxResults=0).execute(num_retries=MAX_ATTEMPTS)
    if not builds:
      raise AndroidBuildFetchError(
          'Failed to locate build with branch %s, build id %s and target %s.' %
          (branch, build_id, target))

  @classmethod
  def GetArtifacts(cls, branch, build_id, target):
    """Get the list of artifacts for given build id and target.

    The return value is a list of dictionaries, each containing information
    about an artifact.
    For example:
        {u'contentType': u'application/octet-stream',
         u'crc32': 4131231264,
         u'lastModifiedTime': u'143518405786',
         u'md5': u'c04c823a64293aa5bf508e2eb4683ec8',
         u'name': u'fastboot',
         u'revision': u'HsXLpGsgEaqj654THKvR/A==',
         u'size': u'6999296'},

    Args:
      branch: branch of the desired build.
      build_id: Build id of the Android build, e.g., 2155602.
      target: Target of the Android build, e.g., shamu-userdebug.

    Returns:
      A list of artifacts for given build id and target.
    """
    service_obj = cls._GetServiceObject()
    cls._VerifyBranch(service_obj, branch, build_id, target)

    # Get all artifacts for the given build_id and target.
    artifacts = service_obj.buildartifact().list(
        buildType='submitted', buildId=build_id, target=target,
        attemptId='latest', maxResults=0).execute(num_retries=MAX_ATTEMPTS)
    return artifacts['artifacts']

  @classmethod
  @retry.retry(Exception, timeout_min=DOWNLOAD_TIMEOUT_MINS)
  def Download(cls, branch, build_id, target, resource_id, dest_file):
    """Download the list of artifacts for given build id and target.

    Args:
      branch: branch of the desired build.
      build_id: Build id of the Android build, e.g., 2155602.
      target: Target of the Android build, e.g., shamu-userdebug.
      resource_id: Name of the artifact to donwload.
      dest_file: Path to the file to download to.
    """
    service_obj = cls._GetServiceObject()
    cls._VerifyBranch(service_obj, branch, build_id, target)

    # Delete partially downloaded file if exists.
    subprocess.call(['rm', '-rf', dest_file])

    # TODO(dshi): Add retry logic here to avoid API flakes.
    download_req = service_obj.buildartifact().get_media(
        buildType='submitted', buildId=build_id, target=target,
        attemptId='latest', resourceId=resource_id)
    with io.FileIO(dest_file, mode='wb') as fh:
      downloader = apiclient.http.MediaIoBaseDownload(
          fh, download_req, chunksize=DEFAULT_CHUNKSIZE)
      done = None
      while not done:
        _, done = downloader.next_chunk(num_retries=MAX_ATTEMPTS)


  @classmethod
  @retry.retry(Exception, timeout_min=QUERY_TIMEOUT_MINS,
               blacklist=[AndroidBuildFetchError])
  def GetLatestBuildID(cls, target, branch):
    """Get the latest build ID for the given target and branch.

    Args:
      branch: branch of the desired build.
      target: Target of the Android build, e.g., shamu-userdebug.

    Returns:
      Build id of the latest successful Android build for the given target and
      branch, e.g., 2155602.
    """
    service_obj = cls._GetServiceObject()
    builds = service_obj.build().list(
        buildType='submitted', branch=branch, target=target, successful=True,
        maxResults=1).execute(num_retries=MAX_ATTEMPTS)
    if not builds or not builds['builds']:
      raise AndroidBuildFetchError(
          'Failed to locate build with branch %s and target %s.' %
          (branch, target))
    return builds['builds'][0]['buildId']