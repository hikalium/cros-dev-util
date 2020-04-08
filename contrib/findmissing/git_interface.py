#!/usr/bin/env python3
# -*- coding: utf-8 -*-"
#
# Copyright 2020 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Module containing methods interfacing with git

i.e Parsing git logs for change-id, full commit sha's, etc.
"""

from __future__ import print_function
import os
import re
import subprocess
import common


def get_upstream_fullsha(abbrev_sha):
    """Returns the full upstream sha for an abbreviated 12 digit sha using git cli"""
    upstream_absolute_path = common.get_kernel_absolute_path(common.UPSTREAM_PATH)
    try:
        cmd = ['git', '-C', upstream_absolute_path, 'rev-parse', abbrev_sha]
        full_sha = subprocess.check_output(cmd, encoding='utf-8')
        return full_sha.rstrip()
    except subprocess.CalledProcessError as e:
        raise type(e)('Could not find full upstream sha for %s' % abbrev_sha, e.cmd) from e


def get_commit_message(kernel_path, sha):
    """Returns the commit message for a sha in a given local path to kernel."""
    try:
        cmd = ['git', '-C', kernel_path, 'log',
                '--format=%B', '-n', '1', sha]
        commit_message = subprocess.check_output(cmd, encoding='utf-8', errors='ignore')
        return commit_message
    except subprocess.CalledProcessError as e:
        raise type(e)('Couldnt retrieve commit in kernel path %s for sha %s'
                        % (kernel_path, sha), e.cmd) from e


def get_upstream_commit_message(upstream_sha):
    """Returns the commit message for a given upstream sha using git cli."""
    upstream_absolute_path = common.get_kernel_absolute_path(common.UPSTREAM_PATH)
    return get_commit_message(upstream_absolute_path, upstream_sha)


def get_chrome_commit_message(chrome_sha):
    """Returns the commit message for a given chrome sha using git cli."""
    chrome_absolute_path = common.get_kernel_absolute_path(common.CHROMEOS_PATH)
    return get_commit_message(chrome_absolute_path, chrome_sha)


def get_commit_changeid_linux_chrome(kernel_sha):
    """Returns the changeid of the kernel_sha commit by parsing linux_chrome git log.

    kernel_sha will be one of linux_stable or linux_chrome commits.
    """
    chrome_absolute_path = common.get_kernel_absolute_path(common.CHROMEOS_PATH)
    try:
        cmd = ['git', '-C', chrome_absolute_path, 'log', '--format=%B', '-n', '1', kernel_sha]
        commit_message = subprocess.check_output(cmd, encoding='utf-8', errors='ignore')

        m = re.findall('^Change-Id: (I[a-z0-9]{40})$', commit_message, re.M)

        # Get last change-id in case chrome sha cherry-picked/reverted into new commit
        return m[-1]
    except subprocess.CalledProcessError as e:
        raise type(e)('Couldnt retrieve changeid for commit %s' % kernel_sha, e.cmd) from e
    except IndexError as e:
        # linux_stable kernel_sha's do not have an associated ChangeID
        return None


def get_last_commit_sha_linux_chrome():
    """Retrieves the last SHA in linux_chrome repository."""
    chrome_absolute_path = common.get_kernel_absolute_path(common.CHROMEOS_PATH)
    try:
        cmd = ['git', '-C', chrome_absolute_path, 'rev-parse', 'HEAD']
        last_commit = subprocess.check_output(cmd, encoding='utf-8')
        return last_commit.rstrip()
    except subprocess.CalledProcessError as e:
        raise type(e)('Couldnt retrieve most recent commit in linux_chrome', e.cmd) from e


def get_git_push_cmd(chromeos_branch, reviewers):
    """Generates git push command with added reviewers and autogenerated tag.

    Read more about gerrit tags here:
        https://gerrit-review.googlesource.com/Documentation/cmd-receive-pack.html
    """
    git_push_head = 'git push origin HEAD:refs/for/%s' % chromeos_branch
    reviewers_tag = ['r=%s'% r for r in reviewers]
    autogenerated_tag = ['t=autogenerated']
    tags = ','.join(reviewers_tag + autogenerated_tag)
    return git_push_head + '%' + tags


def cherry_pick_and_push_fix(fixer_upstream_sha, chromeos_branch,
                                fix_commit_message, reviewers):
    """Cherry picks upstream commit into chrome repo.

    Adds reviewers and autogenerated tag with the pushed commit.
    """
    cwd = os.getcwd()
    chrome_absolute_path = common.get_kernel_absolute_path(common.CHROMEOS_PATH)

    # reset linux_chrome repo to remove local changes
    try:
        os.chdir(chrome_absolute_path)
        subprocess.run(['git', 'checkout', chromeos_branch], check=True)
        subprocess.run(['git', 'reset', '--hard', 'origin/%s' % chromeos_branch], check=True)
        subprocess.run(['git', 'cherry-pick', '-n', fixer_upstream_sha], check=True)
        subprocess.run(['git', 'commit', '-s', '-m', fix_commit_message], check=True)

        # commit has been cherry-picked and committed locally, precommit hook
        #  in git repository adds changeid to the commit message
        last_commit = get_last_commit_sha_linux_chrome()
        fixer_changeid = get_commit_changeid_linux_chrome(last_commit)

        git_push_cmd = get_git_push_cmd(chromeos_branch, reviewers)
        subprocess.run(git_push_cmd.split(' '), check=True)
        subprocess.run(['git', 'reset', '--hard', 'origin/%s' % chromeos_branch], check=True)

        return fixer_changeid
    except subprocess.CalledProcessError as e:
        raise ValueError('Failed to cherrypick and push upstream fix %s on branch %s'
                        % (fixer_upstream_sha, chromeos_branch)) from e
    finally:
        subprocess.run(['git', 'reset', '--hard', 'origin/%s' % chromeos_branch], check=True)
        os.chdir(cwd)