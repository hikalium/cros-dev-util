#!/usr/bin/env python3
# -*- coding: utf-8 -*-"
#
# Copyright 2020 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Module containing methods interfacing with gerrit.

i.e Create new bugfix change tickets, and reading metadata about a specific change.

Example CURL command that creates CL:
curl -b /home/chromeos_patches/.git-credential-cache/cookie \
        --header "Content-Type: application/json" \
        --data \
        '{"project":"chromiumos/third_party/kernel",\
        "subject":"test",\
        "branch":"chromeos-4.19",\
        "topic":"test_topic"}' https://chromium-review.googlesource.com/a/changes/
"""

from __future__ import print_function
import json
import http
import os
import re
import requests

import common
import git_interface


def get_auth_cookie():
    """Load cookies in order to authenticate requests with gerrit/googlesource."""
    # This cookie should exist on GCE in order to perform GAIA authenticated requests
    gerrit_credentials_cookies = http.cookiejar.MozillaCookieJar(common.GIT_COOKIE_PATH, None, None)
    gerrit_credentials_cookies.load()
    return gerrit_credentials_cookies


def retrieve_and_parse_endpoint(endpoint_url):
    """Retrieves Gerrit endpoint response and removes XSSI prefix )]}'"""
    try:
        resp = requests.get(endpoint_url, cookies=get_auth_cookie())
        resp.raise_for_status()
        resp_json = json.loads(resp.text[5:])
    except requests.exceptions.HTTPError as e:
        raise type(e)('Endpoint %s should have HTTP response 200' % endpoint_url) from e
    except json.decoder.JSONDecodeError as e:
        raise ValueError('Response should contain json )]} prefix to prevent XSSI attacks') from e

    return resp_json


def set_and_parse_endpoint(endpoint_url, payload=None):
    """POST request to gerrit endpoint with specified payload."""
    try:
        resp = requests.post(endpoint_url, json=payload, cookies=get_auth_cookie())
        resp.raise_for_status()
        resp_json = json.loads(resp.text[5:])
    except json.decoder.JSONDecodeError as e:
        raise ValueError('Response should contain json )]} prefix to prevent XSSI attacks') from e

    return resp_json


def get_reviewers(changeid):
    """Retrieves list of reviewer emails from gerrit given a chromeos changeid."""
    list_reviewers_endpoint = os.path.join(common.CHROMIUM_REVIEW_BASEURL, 'changes',
                                        changeid, 'reviewers')

    resp = retrieve_and_parse_endpoint(list_reviewers_endpoint)

    try:
        return [reviewer_resp['email'] for reviewer_resp in resp]
    except KeyError as e:
        raise type(e)('Gerrit API endpoint to list reviewers should contain key email') from e


def set_reviewers(changeid, reviewer_emails):
    """Adds reviewers to a Gerrit CL."""
    add_reviewer_endpoint = os.path.join(common.CHROMIUM_REVIEW_BASEURL, 'changes',
                                        changeid, 'reviewers')

    for email in reviewer_emails:
        payload = {'reviewer': email}
        set_and_parse_endpoint(add_reviewer_endpoint, payload)


def abandon_change(changeid, reason=None):
    """Abandons a change."""
    abandon_change_endpoint = os.path.join(common.CHROMIUM_REVIEW_BASEURL, 'changes',
                                            changeid, 'abandon')

    abandon_payload = {'message': reason} if reason else None

    try:
        set_and_parse_endpoint(abandon_change_endpoint, abandon_payload)
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 409:
            print('Change %s has already been abandoned' % changeid)
        else:
            raise


def restore_change(changeid):
    """Restores an abandoned change."""
    restore_change_endpoint = os.path.join(common.CHROMIUM_REVIEW_BASEURL, 'changes',
                                            changeid, 'restore')
    set_and_parse_endpoint(restore_change_endpoint)


def get_change(changeid):
    """Retrieves ChangeInfo from gerrit using its changeid"""
    get_change_endpoint = os.path.join(common.CHROMIUM_REVIEW_BASEURL, 'changes',
                                        changeid)
    return retrieve_and_parse_endpoint(get_change_endpoint)


def set_hashtag(changeid):
    """Set hashtag to be autogenerated indicating a robot generated CL."""
    set_hashtag_endpoint = os.path.join(common.CHROMIUM_REVIEW_BASEURL, 'changes',
                                        changeid, 'hashtags')
    hashtag_input_payload = {'add' : ['autogenerated']}
    set_and_parse_endpoint(set_hashtag_endpoint, hashtag_input_payload)

def get_status(changeid):
    """Retrieves the latest status of a changeid by checking gerrit."""
    change_info = get_change(changeid)
    return change_info['status']

def get_bug_test_line(chrome_sha):
    """Retrieve BUG and TEST lines from the chrome sha."""
    # stable fixes don't have a fixee changeid
    bug_test_line = 'BUG=%s\nTEST=%s'
    bug = test = None
    if not chrome_sha:
        return bug_test_line % (bug, test)

    chrome_commit_msg = git_interface.get_chrome_commit_message(chrome_sha)

    bug_matches = re.findall('^BUG=(.*)$', chrome_commit_msg, re.M)
    test_matches = re.findall('^TEST=(.*)$', chrome_commit_msg, re.M)

    bug = bug_matches[0] if bug_matches else None
    test = test_matches[0] if test_matches else None

    return bug_test_line % (bug, test)


def generate_fix_message(fixer_upstream_sha, bug_test_line):
    """Generates new commit message for a fix change.

    Use script ./contrib/from_upstream.py to generate new commit msg
    Commit message should include essential information:
    i.e:
        FROMGIT, FROMLIST, ANDROID, CHROMIUM, etc.
        commit message indiciating what is happening
        BUG=...
        TEST=...
        tag for Fixes: <upstream-sha>
    """
    fix_upstream_commit_msg = git_interface.get_upstream_commit_message(fixer_upstream_sha)

    upstream_full_sha = git_interface.get_upstream_fullsha(fixer_upstream_sha)
    cherry_picked = '(cherry picked from commit %s)\n\n'% upstream_full_sha


    commit_message = ('UPSTREAM: {fix_commit_msg}'
                      '{cherry_picked}'
                      '{bug_test_line}').format(fix_commit_msg=fix_upstream_commit_msg,
                        cherry_picked=cherry_picked, bug_test_line=bug_test_line)

    return commit_message


# Note: Stable patches won't have a fixee_change_id since they come into chromeos as merges
def create_change(fixee_kernel_sha, fixer_upstream_sha, branch):
    """Creates a Patch in gerrit given a ChangeInput object.

    Determines whether a change for a fix has already been created,
    and avoids duplicate creations.
    """
    cwd = os.getcwd()
    chromeos_branch = common.chromeos_branch(branch)

    # fixee_changeid will be None for stable fixee_kernel_sha's
    fixee_changeid = git_interface.get_commit_changeid_linux_chrome(fixee_kernel_sha)

    # if fixee_changeid is set, the fixee_kernel_sha represents a chrome sha
    chrome_kernel_sha = fixee_kernel_sha if fixee_changeid else None

    bug_test_line = get_bug_test_line(chrome_kernel_sha)
    fix_commit_message = generate_fix_message(fixer_upstream_sha, bug_test_line)

    try:
        # Cherry pick changes and generate commit message indicating fix from upstream
        fixer_changeid = git_interface.cherry_pick_and_push_fix(fixer_upstream_sha,
                                                    chromeos_branch, fix_commit_message)
    except ValueError:
        print('Failed to create gerrit ticket for [fixee_kernel_sha, fixer_upstream_sha]',
                (fixee_kernel_sha, fixer_upstream_sha))
        raise

    # TODO(hirthanan): find relevant mailing list/reviewers
    # For now we will assign it to a default user like Guenter?
    # This is for stable bug fix patches that don't have a direct fixee changeid
    #  since groups of stable commits get merged as one changeid
    reviewers = ['groeck@chromium.org']
    try:
        if fixee_changeid:
            cl_reviewers = get_reviewers(fixee_changeid)
            reviewers = cl_reviewers if cl_reviewers else reviewers
    except requests.exceptions.HTTPError:
        print('Error getting reviewers from gerrit for fixee_changeid', fixee_changeid)

    set_reviewers(fixer_changeid, reviewers)

    os.chdir(cwd)
    return fixer_changeid
