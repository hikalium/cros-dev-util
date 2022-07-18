#!/usr/bin/env python3

# Copyright 2022 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

# Disable pylint noise
# pylint: disable=import-error
# pylint: disable=redefined-outer-name
# pylint: disable=input-builtin
# pylint: disable=broad-except

"""Creates a bisection branch between two KCR results"""

from datetime import datetime
import getopt
import re
import sys

from buildhelpers import verify_build
from githelpers import checkout
from githelpers import cherry_pick
from githelpers import commit_message
from githelpers import commit_subject
from githelpers import create_head
from githelpers import diff
from githelpers import generic_abort
from githelpers import generic_continue
from githelpers import is_merge
from githelpers import is_resolved
from githelpers import list_shas
from githelpers import patch_title
from githelpers import revert
import sh


FIXUP_PREFIX = 'FIXUP: '
FROMLIST_PREFIX = 'FROMLIST: '
FROMGIT_PREFIX = 'FROMGIT: '

skip_reverts = [
    'kernel-rebase: normalization [autogenerated]'
]

debug = 0

def kernelupstream_branch(ver):
    """Map kernel version to branch name."""
    branch_prefix = 'cros/merge/continuous/chromeos-kernelupstream-'
    return f'{branch_prefix}{ver}'

def get_patches(ver):
    """List of patches above upstream tag.

    Each patch is described as a dictionary with sha, content-hash,
    commit-title and change-id fields.
    """

    branch = kernelupstream_branch(ver)

    checkout('kernel-upstream', branch)
    shas = list_shas('kernel-upstream', f'v{ver}..HEAD')
    shas_cnt = len(shas)

    print(f'Processing {shas_cnt} patches from {branch}...')

    res = []
    for sha in shas:
        content_hash = patch_title('kernel-upstream', sha)
        commit_title = commit_subject('kernel-upstream', sha)

        commit_msg = commit_message('kernel-upstream', sha).splitlines()
        change_id_prefix = 'Change-Id: '
        change_id = None
        for msg_line in commit_msg:
            line = msg_line.strip()
            if line.startswith(change_id_prefix):
                change_id = line[len(change_id_prefix):]
                break

        entry = {}
        entry['sha'] = sha
        entry['content-hash'] = content_hash
        entry['commit-title'] = commit_title
        entry['change-id'] = change_id
        res.append(entry)

    print('Done.')

    res.reverse()
    return res

def is_same(patch1, patch2):
    """Decides whether two patches are the same change.

    The patches might be different in content due to the rebase,
    hence this function uses Change-Ids for comparison if available,
    or patch titles if not.
    """

    chid1 = patch1['change-id']
    chid2 = patch2['change-id']
    title1 = patch1['commit-title']
    title2 = patch2['commit-title']

    # prioritize change-id for commit comparison if available
    if chid1 is not None and chid2 is not None:
        return chid1 == chid2
    return title1 == title2

def is_patch_upstreamed(patches_upstream, patch):
    """Checks if patch is included in the upstream"""

    for entry in patches_upstream:
        if (patch['commit-title'] == entry['commit-title'] or
            patch['commit-title'].strip(FROMLIST_PREFIX) == entry['commit-title'] or
            patch['commit-title'].strip(FROMGIT_PREFIX) == entry['commit-title']):
            if debug:
                print(f'Patch is included in upstream {patch} -> {entry}\n')
            return True

    return False

def assert_empty(sha, is_commit_expected=0):
    """True=empty, false=non-empty"""

    try:
        cherry_pick('kernel-upstream', sha, use_am=False)
        return bool(is_commit_expected)
    except Exception:
        if not is_resolved('kernel-upstream'):
            generic_abort('kernel-upstream')
            return False

    return True


def speculative_check_forward(old, fixup_old, new, fixup_new):
    """Speculative check forward"""

    # In order to verify whether replace disposition introduces any changes
    # apply patches in the following order
    # old -> fixup_old -> new -> fixup_new
    # or
    # fixup_old -> fixup_new
    # in case when disposition holds fixup replace only
    if old is not None:
        checkout('kernel-upstream', old)
    else:
        checkout('kernel-upstream', fixup_old)

    if old is not None:
        if not assert_empty(new):
            return True
        if fixup_old is not None and not assert_empty(fixup_old, 1):
            return True
        if fixup_new is not None and not assert_empty(fixup_new):
            return True
    else:
        if not assert_empty(fixup_new):
            return True

    return False

def speculative_check_reverse(old, fixup_old, new, fixup_new):
    """Speculative check reverse"""

    # To verify if disposition introduces any changes apply
    # patches in reverse ordear. The aim of this operation is
    # to catch a case when new/fixup_new patches are a subset
    # of old/ixup_old patches
    # new -> fixup_new -> old -> fixup_old
    # or
    # fixup_new -> fixup_old
    # in case when disposition holds fixup replace only
    if new is not None:
        checkout('kernel-upstream', new)
    else:
        checkout('kernel-upstream', fixup_new)

    if new is not None:
        if not assert_empty(old):
            return True
        if fixup_new is not None and not assert_empty(fixup_new, 1):
            return True
        if fixup_old is not None and not assert_empty(fixup_old):
            return True
    else:
        if not assert_empty(fixup_old):
            return True

    return False

def speculative_check(disp):
    """True=retain, False=skip"""

    old = disp['old']
    new = disp['new']
    fixup_old = disp['fixup_old']
    fixup_new = disp['fixup_new']

    # Validate disposition
    if old is None and new is not None:
        raise AssertionError()
    if old is not None and new is None:
        raise AssertionError()
    if fixup_old is None and fixup_new is not None:
        raise AssertionError()
    if fixup_old is not None and fixup_new is None:
        raise AssertionError()
    if old is None and fixup_old is None:
        raise AssertionError()

    if speculative_check_forward(old, fixup_old, new, fixup_new):
        return True
    if speculative_check_reverse(old, fixup_old, new, fixup_new):
        return True

    return False

def filter_noops(disps):
    """Removes dispositions that don't pass speculative_check(_)"""

    result = []
    i = 0
    for d in disps:
        if (d['disposition'] != 'replace' and
           d['disposition'] != 'replace-fixup'):
            result.append(d)
            continue

        if speculative_check(d):
            result.append(d)
            print('.', end='')
        else:
            print('X', end='')

        if (i + 1) % 8 == 0:
            print()
        else:
            sys.stdout.flush()
        i += 1
    print()

    if debug:
        print('========== DEBUG ==========')
        print('Replace dispositions which passed filter_noops:')
        for i, d in enumerate(result):
            if (d['disposition'] == 'replace' or
               d['disposition'] == 'replace-fixup'):
                print(f'{i}.{d}\n')
        print('===========================')

    return result

def dispositions(patches_begin, patches_end, patches_upstream):
    """List a sequence of ChromeOS patch operations that transform {begin} into {end}."""

    # Collect all content-hashes that are duplicated across the two lists.
    dupe_content_hashes = set()
    for patch1 in patches_begin:
        for patch2 in patches_end:
            if patch1['content-hash'] == patch2['content-hash']:
                dupe_content_hashes.add(patch1['content-hash'])

    # Remove the duplicates from both lists.
    # This also removes all empty commits as the content-hash ignores
    # commit messages, and there are many of them on both branches.
    diff_patches_begin = []
    for patch in patches_begin:
        if patch['content-hash'] not in dupe_content_hashes:
            diff_patches_begin.append(patch)

    diff_patches_end = []
    for patch in patches_end:
        if patch['content-hash'] not in dupe_content_hashes:
            diff_patches_end.append(patch)

    # Prepare a sequence of dispositions to trasnform the private
    # ChromeOS patches state from {begin} into that from {end}
    dispositions_naive = []
    for patch in diff_patches_begin:
        dispositions_naive.append({'disposition': 'revert', 'patch': patch})
    for patch in diff_patches_end:
        dispositions_naive.append({'disposition': 'pick', 'patch': patch})

    # Look for replacements, i.e. patches different on {begin} and {end}
    # They will be squashed together
    to_squash = []
    for disp1 in dispositions_naive:
        for disp2 in dispositions_naive:
            d1 = disp1['disposition']
            d2 = disp2['disposition']
            patch1 = disp1['patch']
            patch2 = disp2['patch']

            is_fixup = patch1['commit-title'].startswith(FIXUP_PREFIX)
            # squash pairs of revert-apply other than fixups
            if d1 == 'revert' and d2 == 'pick' and is_same(patch1, patch2) and not is_fixup:
                to_squash.append({'revert': patch1, 'pick': patch2})

    # Rewords the dispositions so that instead of simple pick/revert a wider
    # Array of operations is supported:
    # - Pick:
    #   * fixup_old: a fixup previously applied to the patch, reverted before pick
    #   * fixup_new: a fixup supposed to be applied to the patch, applied after pick
    #   * sha: sha of commit to pick
    #   * title: subject of the patch
    # - Revert:
    #   * sha: sha of commit to revert
    #   * title: subject of the patch
    # - Replace:
    #   * fixup_old: a fixup previously applied to the patch, reverted before revert of old
    #   * fixup_new: a fixup supposed to be applied to the patch, applied after pick of new
    #   * old: sha of patch as of {begin}
    #   * new: sha of patch as of {end}
    #   * title: subject of old
    # - Replace-fixup:
    #   * fixup_old: a fixup to be reverted
    #   * fixup_new: a fixup to be applied
    #   * title: subject of the fixup
    #
    # The fixup fields will be populated later
    dispositions = []
    for disp in dispositions_naive:
        d = disp['disposition']
        patch = disp['patch']
        if d == 'revert':
            squashed = False
            upstreamed = False
            for squash in to_squash:
                if (is_same(patch, squash['revert']) and patch['content-hash'] and
                   squash['pick']['content-hash']):
                    dispositions.append({
                        'disposition': 'replace',
                        'old': patch['sha'],
                        'new': squash['pick']['sha'],
                        'fixup_old': None,
                        'fixup_new': None,
                        'title': patch['commit-title']
                    })
                    squashed = True
                    break

            if not squashed:
                upstreamed = is_patch_upstreamed(patches_upstream, patch)

            if not squashed and not upstreamed:
                dispositions.append({
                    'disposition': 'revert',
                    'sha': patch['sha'],
                    'title': patch['commit-title']
                })
        elif d == 'pick':
            skip = False
            for squash in to_squash:
                if is_same(patch, squash['pick']):
                    skip = True
                    break
            if not skip:
                dispositions.append({
                    'disposition': 'pick',
                    'sha': patch['sha'],
                    'fixup_old': None,
                    'fixup_new': None,
                    'title': patch['commit-title']
                })

    # Populate the fixup_* fields and mark the moved fixups for
    # removal from individual dispositions.
    disps_to_skip = []
    for d1 in dispositions:
        disp = d1['disposition']
        field = None
        if disp == 'revert':
            field = 'fixup_old'
        elif disp == 'pick':
            field = 'fixup_new'

        if d1['title'].startswith(FIXUP_PREFIX):
            title = d1['title'].strip(FIXUP_PREFIX)
            for d2 in dispositions:
                if d2['title'] == title:
                    d2[field] = d1['sha']
                    disps_to_skip.append(d1)
    if debug:
        print('========== DEBUG ==========')
        print('Fixups to skip:')
        for i, d in enumerate(disps_to_skip):
            print(f'{i}.{d}\n')
        print('===========================')

    # Remove the fixups identified above.
    dispositions = [d for d in dispositions if d not in disps_to_skip]

    # Search for fixup replacements only
    disps_to_skip.clear()
    for d1 in dispositions:
        is_fixup = d1['title'].startswith(FIXUP_PREFIX)
        for d2 in dispositions:
            if is_fixup and d1['title'] == d2['title']:
                if (d1['disposition'] == 'revert' and d2['disposition'] == 'pick'):
                    dispositions.append({
                        'disposition': 'replace-fixup',
                        'old': None,
                        'new': None,
                        'fixup_old': d1['sha'],
                        'fixup_new': d2['sha'],
                        'title': d1['title']
                    })
                    disps_to_skip.append(d1)
                    disps_to_skip.append(d2)
    if debug:
        print('========== DEBUG ==========')
        print('Fixup replacements:')
        l1 = disps_to_skip[::2]
        l2 = disps_to_skip[1::2]
        for i, d in enumerate(l1):
            dn = l2[i]
            print(f'{i}.{d} -> {dn}\n')
        print('===========================')

    # Remove the dispositions identified above
    dispositions = [d for d in dispositions if d not in disps_to_skip]

    return dispositions

def upstream_picks(begin, end):
    """Lists all upstream commits between {begin} and {end}"""

    tag1 = f'v{begin}'
    tag2 = f'v{end}'

    checkout('kernel-upstream', tag2)
    shas = list_shas('kernel-upstream', f'{tag1}..HEAD')

    shas.reverse()

    upstream = []
    for sha in shas:
        entry = {}
        entry['sha'] = sha
        entry['commit-title'] = commit_subject('kernel-upstream', sha)
        upstream.append(entry)

    # skip merges, as they can't be cherry-picked directly
    # and are always empty on upstream.
    return [entry for entry in upstream if not is_merge('kernel-upstream', entry['sha'])]

def handle_error(e):
    """UI for interaction with conflicts and other errors"""

    while True:
        print('Conflict occurred')
        print('Options:')
        print('c/continue -- proceed, type after resolving the conflict')
        print('s/stop -- halt the entire process')
        print('d/drop -- drop the patch')
        print('?/what -- print the exception')

        cmd = ''
        while cmd not in ['c', 'continue', 's', 'stop', 'd', 'drop', '?', 'what']:
            cmd = input()
        if cmd in ['c', 'continue']:
            if not is_resolved('kernel-upstream'):
                print('Something still not resolved. Resolve and press c.')
                continue
            generic_continue('kernel-upstream')
            return 'c'
        if cmd in ['s', 'stop']:
            sys.exit(-1)
        if cmd in ['d', 'drop']:
            generic_abort('kernel-upstream')
            return 'd'
        if cmd in ['?', 'what']:
            print(e)

def squash(top_patches):
    """Squashes len(top_patches) commits

    The commit message is the top_patches list formatted in a human-readable way.
    This list would best reflect the subjects of the squashed commits, but it can
    be anything as long as it's a list of strings.
    """

    n = len(top_patches)
    msg = 'Squash: ['
    for patch in top_patches:
        msg += patch
        msg += ', '
    msg += ']'

    with sh.pushd('kernel-upstream'):
        sh.git('reset', f'HEAD~{n}')

        err = None
        try:
            sh.git('add', '-A')
            sh.git('commit', '-m', msg)
        except sh.ErrorReturnCode_1 as e:
            if 'nothing to commit' in str(e):
                print('Replace result is null, proceed without commit')
                return False
            err = e
        except Exception as e:
            err = e

        if err is not None:
            handle_error(e)

    return False

def revert_sha(sha):
    """Revert sha"""

    try:
        revert('kernel-upstream', sha)
        return True
    except Exception as e:
        choice = handle_error(e)
        if choice == 'c':
            return True

    return False

def cherry_pick_sha(sha, use_am=False):
    """Cherry pick sha"""

    try:
        cherry_pick('kernel-upstream', sha, use_am=use_am)
        return True
    except Exception as e:
        if '--allow-empty' in str(e):
            print('Nothing to commit, skipping')
            return True
        if 'The previous cherry-pick is now empty' in str(e):
            print('cherry-pick empty')
            return True
        choice = handle_error(e)
        if choice == 'c':
            return True

    return False

def create_bisect_branch(begin, end):
    """Create bisection branch"""

    # Resultant branch name format
    bisect_branch = f'kernelupstream-bisect-{begin}-{end}'

    print('Begin work on constructing a bisection branch...')
    print(f'Checkout {begin}')
    checkout('kernel-upstream', kernelupstream_branch(begin))
    print(f'Create branch {bisect_branch}')
    create_head('kernel-upstream', bisect_branch)

    # List ChromeOS
    print(f'List ChromeOS patches for {kernelupstream_branch(begin)}')
    begin_patches = get_patches(begin)
    print(f'List ChromeOS patches for {kernelupstream_branch(end)}')
    end_patches = get_patches(end)

    # List upstream patches between {begin} and {end}
    print(f'List upstream patches between {begin} and {end}')
    from_upstream = upstream_picks(begin, end)

    print('Calculating dispositions')
    disps = dispositions(begin_patches, end_patches, from_upstream)

    print('Removing no-op replaces')
    disps = filter_noops(disps)

    reverts = 0
    picks = 0
    replacements = 0
    for disp in disps:
        d = disp['disposition']
        if d == 'revert':
            reverts += 1
        elif d == 'pick':
            picks += 1
        elif d == 'replace':
            replacements += 1

    print('Computed dispositions of ChromeOS patches:')
    print(f'Patches to revert: {reverts}')
    print(f'Patches to pick: {picks}')
    print(f'Patches to replace: {replacements}')
    from_upstream_count = len(from_upstream)
    print(f'Patches that entered upstream between {begin} and {end}: {from_upstream_count}')
    print()

    # Checkout bisection branch
    checkout('kernel-upstream', bisect_branch)

    print('===========================')
    print('Revert unneeded ChromeOS patches')
    for disp in disps:
        if disp['disposition'] != 'revert':
            continue
        if disp['title'] in skip_reverts:
            continue

        print('Revert', disp['sha'], disp['title'])
        revert_sha(disp['sha'])

    print('===========================')
    print('Cherry-pick upstream patches')
    for entry in from_upstream:
        print('Pick', entry['sha'], entry['commit-title'])
        cherry_pick_sha(entry['sha'])

    print('===========================')
    print('Replace changed ChromeOS patches')
    for disp in disps:
        if disp['disposition'] != 'replace':
            continue

        to_revert = disp['old']
        to_pick = disp['new']
        title = disp['title']
        print(f'Replace {to_revert} -> {to_pick} {title}')

        fixup_old = disp['fixup_old']
        fixup_new = disp['fixup_new']

        applied = []
        if fixup_old is not None:
            title = commit_subject('kernel-upstream', fixup_old)
            print(f'Revert old fixup {fixup_old} {title}')
            revert_sha(fixup_old)
            applied.append(commit_subject('kernel-upstream', fixup_old))

        title = commit_subject('kernel-upstream', to_revert)
        print(f'Revert commit {to_revert} {title}')
        revert_sha(to_revert)
        applied.append(commit_subject('kernel-upstream', to_revert))

        title = commit_subject('kernel-upstream', to_pick)
        print(f'Pick commit {to_pick} {title}')
        merge = is_merge('kernel-upstream', to_pick)
        choice = cherry_pick_sha(to_pick, merge)
        if choice == 'd':
            with sh.pushd('kernel-upstream'):
                rollback = len(applied)
                sh.git('reset', '--hard', f'HEAD~{rollback}')
            continue
        applied.append(commit_subject('kernel-upstream', to_pick))

        if fixup_new is not None:
            title = commit_subject('kernel-upstream', fixup_new)
            print(f'Pick new fixup {fixup_new} {title}')
            choice = cherry_pick_sha(fixup_new)
            if choice == 'd':
                with sh.pushd('kernel-upstream'):
                    rollback = len(applied)
                    sh.git('reset', '--hard', f'HEAD~{rollback}')
                continue
            applied.append(commit_subject('kernel-upstream', fixup_new))

        if len(applied) > 1:
            squash(applied)

    print('===========================')
    print('Replace changed ChromeOS fixups')
    for disp in disps:
        if disp['disposition'] != 'replace-fixup':
            continue
        if not disp['title'].startswith(FIXUP_PREFIX):
            continue

        fixup_old = disp['fixup_old']
        fixup_new = disp['fixup_new']
        title = disp['title']
        print(f'Replace fixup {fixup_old} -> {fixup_new} {title}')

        revert_sha(fixup_old)
        cherry_pick_sha(fixup_new)

    print('===========================')
    print('Pick ChromeOS patches')
    for disp in disps:
        if disp['disposition'] != 'pick':
            continue

        print('Pick', disp['sha'], disp['title'])
        cherry_pick_sha(disp['sha'])

    # Apply a special patch to account for any remaining difference between this bisection
    # branch and the {end}.
    print('===========================')
    print(f'Creating a final commit to make the tree exactly the same as {end}')
    end_branch = kernelupstream_branch(end)
    rem_diff = diff('kernel-upstream', f'HEAD..{end_branch}')
    rem_diff_path = '/tmp/kcr_bisect_rem.patch'
    with open(rem_diff_path, 'w') as f:
        f.write(rem_diff)
    with sh.pushd('kernel-upstream'):
        sh.git('apply', rem_diff_path)
        sh.git('add', '-A')
        sh.git('commit', '-m', f'KCR BISECT: Commit all remaining diff from {end}')

def verify_bisect_branch(begin, end, steps_cnt):
    """Verify bisection branch"""

    # Resultant branch name format
    bisect_branch = f'kernelupstream-bisect-{begin}-{end}'

    print(f'Checkout {bisect_branch}')
    checkout('kernel-upstream', bisect_branch)

    shas = list_shas('kernel-upstream', f'{kernelupstream_branch(begin)}..HEAD')
    shas_cnt = len(shas)
    print(f'There are {shas_cnt} commits on {bisect_branch} branch which '\
          f'will be verified in {steps_cnt} steps\n')

    idx = 0
    step = round(shas_cnt/steps_cnt)
    start_time = datetime.now()
    while idx < shas_cnt:
        start = datetime.now()

        sha = list_shas('kernel-upstream', 'HEAD~1..HEAD')
        title = commit_subject('kernel-upstream', sha)
        print(f'Verifying build with HEAD set at commit {sha[0]} {title}')

        ret = verify_build(None)
        if ret['exit_code'] == 0:
            print('Built succesfully.')
        else:
            print('Error building :')
            if ret['error_line'] is not None:
                l = ret['error_line']
                reg = re.compile('\x1b\\[[0-9;]*m')
                err = reg.sub('', '\n'.join(
                            ret['output'].split('\n')[
                            l - 7:l]))
                print(err)
            else:
                print('(No error line.)')

        idx += step
        if idx < shas_cnt:
            checkout('kernel-upstream', f'HEAD~{step}')

        end = datetime.now()
        diff = end - start
        print(f'Build took {diff}\n')

    end_time = datetime.now()
    print(f'Total verification time {end_time - start_time}')

# Setup begin and end versions
begin = '5.19-rc7'
end = '5.19'

opts, rem = getopt.getopt(sys.argv[1:], 'cvs:', ['create', 'verify', 'steps-num='])

mode = None
steps_cnt = 80
for opt, arg in opts:
    if opt in ['-c', '--create']:
        if mode is not None:
            print('invalid arguments')
            sys.exit(-1)
        mode = 'create'
    if opt in ['-v', '--verify']:
        if mode is not None:
            print('invalid arguments')
            sys.exit(-1)
        mode = 'verify'
    if opt in ['-s', '--steps-num']:
        steps_cnt = int(arg)

if mode == 'create':
    create_bisect_branch(begin, end)
elif mode == 'verify':
    verify_bisect_branch(begin, end, steps_cnt)
