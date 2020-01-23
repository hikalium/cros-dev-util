#!/usr/bin/env python3
# -*- coding: utf-8 -*-"
#
# Copyright 2020 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Module containing shared helper methods."""

from __future__ import print_function

import os
import sqlite3
import re

WORKDIR = os.getcwd()
DBDIR = os.path.join(WORKDIR, 'database')
UPSTREAMDB = os.path.join(DBDIR, 'upstream.db')

# "commit" is sometimes seen multiple times, such as with commit 6093aabdd0ee
CHERRYPICK = re.compile(r'cherry picked from (commit )+([0-9a-f]+)')
STABLE = re.compile(r'^\s*(commit )+([a-f0-9]+) upstream')
STABLE2 = re.compile(r'^\s*\[\s*Upstream (commit )+([0-9a-f]+)\s*\]')


def stabledb(version):
    """Path of stabledb"""
    return os.path.join(DBDIR, 'stable-%s.db' % version)


def chromeosdb(version):
    """Path of chromeosdb"""
    return os.path.join(DBDIR, 'chromeos-%s.db' % version)


def patchdb(version):
    """Path of patchdb for each chromeosdb"""
    return os.path.join(DBDIR, '/patch-%s.db' % version)


def stable_branch(version):
    """Stable branch name"""
    return 'linux-%s.y' % version


def chromeos_branch(version):
    """Chromeos branch name"""
    return 'chromeos-%s' % version


def patch_link(changeID):
    """Link to patch on gerrit"""
    return 'https://chromium-review.googlesource.com/q/%s' % changeID


def doremove(filepath):
    """remove file if it exists"""
    try:
        os.remove(filepath)
    except OSError:
        pass


def make_downstream_table(c):
    """Create database table storing information about chrome/stable git logs"""

    c.execute('CREATE TABLE commits (sha text, usha text, '
            'patchid text, description text)')
    c.execute('CREATE UNIQUE INDEX commit_sha ON commits (sha)')
    c.execute('CREATE INDEX upstream_sha ON commits (usha)')
    c.execute('CREATE INDEX patch_id ON commits (patchid)')


def createdb(db, op):
    """remove and recreate database"""
    newdbdir = os.path.dirname(db)
    os.makedirs(newdbdir, exist_ok=True)

    doremove(db)

    conn = sqlite3.connect(db)
    c = conn.cursor()

    op(c)

    # Convention: table 'tip' ref 1 contains the most recently processed SHA.
    # Use this to avoid re-processing SHAs already in the database.
    c.execute('CREATE TABLE tip (ref integer, sha text)')
    c.execute('INSERT INTO tip (ref, sha) VALUES (?, ?)', (1, ''))

    # Save (commit) the changes
    conn.commit()
    conn.close()
