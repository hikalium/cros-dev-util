# -*-coding: utf-8 -*-

"""Tool for patching cherry-picked commit from LINUX kernel to Chromium OS kernel.
"""

import subprocess
import sys
import os

def get_sha(kernel_path):
    """Returns most recent commit sha"""

    try:
        sha = subprocess.check_output(['git', 'log', '-1', '--format=%H'],
                                      stderr=subprocess.DEVNULL, cwd=kernel_path,
                                      encoding='utf-8')
    except subprocess.CalledProcessError:
        raise PatchApplierException('Sha was not found')

    return sha.rstrip('\n')

def get_commit_message(kernel_path, sha):
    """Returns commit message"""

    try:
        cmd = ['git', '-C', kernel_path, 'log', '--format=%B', '-n', '1', sha]
        commit_message = subprocess.check_output(cmd, encoding='utf-8')

        return commit_message.rstrip() +'\n'
    except subprocess.CalledProcessError:
        raise PatchApplierException('Could not retrieve commit in kernal path %s for sha %s'
                                    % (kernel_path, sha))

def create_commit_message(kernel_path, sha, bug_id):
    """Generates new commit message"""

    bug_test_line = f'BUG=chromium:{bug_id}\nTEST=CQ\n\n'

    org_msg = get_commit_message(kernel_path, sha)

    cherry_picked = f'(cherry picked from commit {sha})\n\n'

    return f'UPSTREAM: {org_msg}{cherry_picked}{bug_test_line}'

def fetch_linux_kernel(kernel_path):
    """Fetch LINUX repo in CHROMIUMOS_KERNEL"""

    if os.getenv('LINUX') == '':
        raise PatchApplierException('Environment variable LINUX is not set')

    try:
        subprocess.check_call(['git', 'fetch', os.getenv('LINUX'), 'master'],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                              cwd=kernel_path)
        return os.getenv('LINUX')
    except subprocess.CalledProcessError as e:
        raise PatchApplierException(e)
    except FileNotFoundError:
        raise PatchApplierException('Kernel is non-existent')

def checkout_branch(kernel, kernel_path):
    """Checking into appropriate branch"""

    try:
        branch = 'cros/chromeos-' + kernel[1:]
        subprocess.check_call(['git', 'checkout', branch], stdout=subprocess.DEVNULL,
                              stderr=subprocess.DEVNULL, cwd=kernel_path)
        subprocess.check_call(['git', 'pull', 'cros', 'chromeos-' + kernel[1:]],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                              cwd=kernel_path)
    except subprocess.CalledProcessError:
        raise PatchApplierException('Checkout failed for %s' % kernel)

def cherry_pick(kernel_path, sha, bug_id):
    """Cherry-picking commit into kernel"""

    fix_commit_message = create_commit_message(kernel_path, sha, bug_id)

    try:
        subprocess.check_output(['git', 'cherry-pick', '-s', sha],
                                stderr=subprocess.PIPE, cwd=kernel_path)
    except subprocess.CalledProcessError as e:
        if 'bad revision' in e.stderr.decode(sys.getfilesystemencoding()):
            raise PatchApplierException('invalid sha %s' % sha)
        subprocess.check_call(['git', 'cherry-pick', '--abort'], cwd=kernel_path)
        return False

    subprocess.check_call(['git', 'commit', '--amend', '-s', '-m', fix_commit_message],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                          cwd=kernel_path)
    return True

def apply_patch(sha, bug_id, kernel_versions):
    """Applies patch from LINUX to Chromium OS kernel"""

    cp_status = {}

    if os.getenv('CHROMIUMOS_KERNEL') == '':
        raise PatchApplierException('Environment variable CHROMIUMOS_KERNEL is not set')

    for kernel in kernel_versions:

        kernel_path = os.path.join(os.getenv('CHROMIUMOS_KERNEL'), kernel)

        fetch_linux_kernel(kernel_path)

        checkout_branch(kernel, kernel_path)

        cp_status[kernel] = cherry_pick(kernel_path, sha, bug_id)

    return cp_status

class PatchApplierException(Exception):
    """Exception raised from PatchApplier."""