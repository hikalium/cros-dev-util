#!/usr/bin/env python3
# -*- coding: utf-8 -*-"
#
# Copyright 2020 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Find missing stable and backported mainline fix patches in chromeos."""

from __future__ import print_function

import MySQLdb # pylint: disable=import-error

import common

DEFAULT_MERGED_REASON = 'Fix merged into linux chrome'


def upstream_fixes_for_shas(db, upstream_shas):
    """Returns list of fixer sha's for a given upstream sha.

    TODO(*): remove this after build_ordered_fixes_table_map moved to SQL CTE
    Note: above todo is blocked by migration to MySQL 5.7, once upgraded then we can switch
    """
    upstream_shas = ["\'" + sha + "\'" for sha in upstream_shas]
    c = db.cursor()

    # format string here since we are inserting n elements
    q = """SELECT fixedby_upstream_sha
            FROM upstream_fixes
            WHERE upstream_sha IN ({})""".format(', '.join(upstream_shas))
    c.execute(q)

    return [a[0] for a in c.fetchall()]


def get_fixes_table_primary_key(db, fixes_table, fix_change_id):
    """Retrieves the primary keys from a fixes table using changeid."""
    c = db.cursor(MySQLdb.cursors.DictCursor)

    q = """SELECT kernel_sha, fixedby_upstream_sha
            FROM {fixes_table}
            WHERE fix_change_id = %s""".format(fixes_table=fixes_table)

    c.execute(q, [fix_change_id])
    row = c.fetchone()
    return (row['kernel_sha'], row['fixedby_upstream_sha'])


def get_fix_status_and_changeid(db, fixes_tables, sha_list, strict):
    """Get branch, fix_change_id, initial_status and status for one or more rows in fixes table."""
    c = db.cursor(MySQLdb.cursors.DictCursor)

    # If sha_list has only one entry, there will be only one database match.
    # Use OR in the query if this is the case.
    if len(sha_list) < 2:
        strict = False

    pre_q = """SELECT '{fixes_table}' AS 'table', branch, kernel_sha, fixedby_upstream_sha,
                      fix_change_id, initial_status, status
               FROM {fixes_table}
               WHERE """

    joined_list = '("'+'","'.join(sha_list)+'")'

    pre_q += ' kernel_sha IN  %s' % joined_list
    pre_q += ' AND' if strict else ' OR'
    pre_q += ' fixedby_upstream_sha IN %s' % joined_list

    q = pre_q.format(fixes_table=fixes_tables.pop(0))
    while fixes_tables:
        q += ' UNION '
        q += pre_q.format(fixes_table=fixes_tables.pop(0))

    c.execute(q)
    return c.fetchall()


def update_change_abandoned(db, fixes_table, kernel_sha, fixedby_upstream_sha, reason=None):
    """Updates fixes_table unique fix row to indicate fix cl has been abandoned.

    Function will only abandon rows in the table which have status OPEN or CONFLICT.
    """
    c = db.cursor()
    q = """UPDATE {fixes_table}
            SET status = 'ABANDONED', close_time = %s, reason = %s
            WHERE kernel_sha = %s
            AND fixedby_upstream_sha = %s
            AND (status = 'OPEN' OR status = 'CONFLICT')""".format(fixes_table=fixes_table)
    close_time = common.get_current_time()
    c.execute(q, [close_time, reason, kernel_sha, fixedby_upstream_sha])
    db.commit()


def update_change_restored(db, fixes_table, kernel_sha, fixedby_upstream_sha, reason=None):
    """Updates fixes_table unique fix row to indicate fix cl has been reopened."""
    rows = get_fix_status_and_changeid(db, [fixes_table], [kernel_sha, fixedby_upstream_sha], True)
    row = rows[0]
    status = 'OPEN' if row['fix_change_id'] else row['initial_status']

    c = db.cursor()
    q = """UPDATE {fixes_table}
            SET status = %s, close_time = %s, reason = %s
            WHERE kernel_sha = %s
            AND fixedby_upstream_sha = %s
            AND status = 'ABANDONED'""".format(fixes_table=fixes_table)
    c.execute(q, [status, None, reason, kernel_sha, fixedby_upstream_sha])
    db.commit()


def update_change_merged(db, fixes_table, kernel_sha, fixedby_upstream_sha,
                            reason=DEFAULT_MERGED_REASON):
    """Updates fixes_table unique fix row to indicate fix cl has been merged."""
    c = db.cursor()
    q = """UPDATE {fixes_table}
            SET status = 'MERGED', close_time = %s, reason = %s
            WHERE kernel_sha = %s
            AND fixedby_upstream_sha = %s""".format(fixes_table=fixes_table)
    close_time = common.get_current_time()
    c.execute(q, [close_time, reason, kernel_sha, fixedby_upstream_sha])
    db.commit()


def update_change_status(db, fixes_table, fix_change_id, status):
    """Updates fixes_table with the latest status from Gerrit API.

    This is done to synchronize CL's that are
    abandoned/restored on Gerrit with our database state
    """
    kernel_sha, fixedby_upstream_sha = get_fixes_table_primary_key(db, fixes_table, fix_change_id)
    if status == common.Status.OPEN:
        update_change_restored(db, fixes_table, kernel_sha, fixedby_upstream_sha)
    elif status == common.Status.ABANDONED:
        update_change_abandoned(db, fixes_table, kernel_sha, fixedby_upstream_sha)
    elif status == common.Status.MERGED:
        update_change_merged(db, fixes_table, kernel_sha, fixedby_upstream_sha)
    else:
        raise ValueError('Change should be either OPEN, ABANDONED, or MERGED')


def update_conflict_to_open(db, fixes_table, kernel_sha, fixedby_upstream_sha, fix_change_id):
    """Updates fixes_table to represent an open change that previously resulted in conflict."""
    c = db.cursor()
    reason = 'Patch applies cleanly after originally conflicting.'
    q = """UPDATE {fixes_table}
            SET status = 'OPEN', fix_change_id = %s, reason = %s
            WHERE kernel_sha = %s
            AND fixedby_upstream_sha = %s""".format(fixes_table=fixes_table)
    c.execute(q, [fix_change_id, reason, kernel_sha, fixedby_upstream_sha])
    db.commit()
