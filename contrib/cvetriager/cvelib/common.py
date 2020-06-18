# -*-coding: utf-8 -*-

"""Module containing shared helper methods."""

import subprocess


class CommonException(Exception):
    """Exception raised from common."""


def get_stable_branch(kernel):
    """Returns stable branch name."""
    branch = kernel[1:]
    return f'linux-{branch}.y'


def get_cros_branch(kernel):
    """Returns chromeos branch name."""
    branch = kernel[1:]
    return f'chromeos-{branch}'


def checkout_branch(kernel, branch, remote, remote_branch, kernel_path):
    """Checks into appropriate branch and keeps it up to date."""
    do_checkout(kernel, branch, kernel_path)
    do_pull(kernel, remote, remote_branch, kernel_path)


def do_checkout(kernel, branch, kernel_path):
    """Checks into given branch."""
    try:
        subprocess.check_call(['git', 'checkout', branch], stdout=subprocess.DEVNULL,
                              stderr=subprocess.DEVNULL, cwd=kernel_path)
    except subprocess.CalledProcessError:
        raise CommonException('Checkout failed for %s' % kernel)


def do_pull(kernel, remote, remote_branch, kernel_path):
    """Pulls from given branch."""
    try:
        subprocess.check_call(['git', 'pull', remote, remote_branch],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                              cwd=kernel_path)
    except subprocess.CalledProcessError:
        raise CommonException('Pull failed for %s' % kernel)