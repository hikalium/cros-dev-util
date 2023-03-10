# Copyright 2020 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Context generator for CVE Triage tool."""

import subprocess
import os
import re
import logging

from cvelib import common, logutils


class ContextGeneratorException(Exception):
    """Exception raised from ContextGenerator."""


class ContextGenerator():
    """Determines which kernels a commit should be applied to."""

    def __init__(self, kernels, check_rel_commits=False, loglvl=logging.DEBUG):
        self.logger = logutils.setuplogging(loglvl, self.__class__.__name__)
        self.kernels = kernels
        self.check_rel_commits = check_rel_commits
        self.relevant_commits = []

    def get_fixes_commit(self, linux_sha):
        """Returns Fixes: tag's commit sha."""
        commit_message = common.get_commit_message(os.getenv('LINUX'), linux_sha)

        # Collects 'Fixes: {sha}' string from commit_message.
        m = re.findall('^Fixes: [a-z0-9]{12}', commit_message, re.M)

        if not m:
            return ''

        split_str = m[0].split(' ')
        sha = split_str[1]

        return sha

    def get_subject_line(self, linux_sha):
        """Returns subject line of given sha."""
        try:
            subject = subprocess.check_output(['git', 'log', '--pretty=format:%s', '-n', '1',
                                              linux_sha], stderr=subprocess.DEVNULL,
                                              cwd=os.getenv('LINUX'), encoding='utf-8')
        except subprocess.CalledProcessError:
            raise ContextGeneratorException(f'Error locating subject for sha {linux_sha}')

        return subject

    def is_in_kernel(self, path, subject, is_inside):
        """Searches through kernel for a given subject."""
        try:
            result = subprocess.check_output(['git', 'log', '--no-merges', '-F', '--grep',
                                             subject], stderr=subprocess.DEVNULL,
                                             cwd=path, encoding='utf-8')
            if bool(result) == is_inside:
                return True
        except subprocess.CalledProcessError:
            pass

        return False

    def filter_fixed_kernels(self, sha):
        """Filters out kernels that are already fixed."""
        valid_kernels = []

        subject = self.get_subject_line(sha)

        for kernel in self.kernels:
            self.logger.debug(f'Checking if {kernel} is fixed with {sha}')

            kernel_path = os.path.join(os.getenv('CHROMIUMOS_KERNEL'), kernel)

            branch = common.get_cros_branch(kernel)
            common.checkout_branch(kernel, f'cros/{branch}', 'cros', branch, kernel_path)

            if self.is_in_kernel(kernel_path, subject, False):
                valid_kernels.append(kernel)

        self.kernels = valid_kernels

    def filter_based_on_stable(self, linux_sha, env_var):
        """Filters out stable or stable-rc kernels with linux commit."""
        valid_kernels = []
        environment = os.getenv(env_var)
        is_rc = bool(env_var == 'STABLE_RC')

        subject = self.get_subject_line(linux_sha)

        for kernel in self.kernels:
            self.logger.debug(f'Checking if {kernel} on {env_var} contains {linux_sha}')

            branch, remote = common.get_stable_branch(kernel, is_rc)

            common.checkout_branch(kernel, branch, 'origin', remote, environment)

            if self.is_in_kernel(environment, subject, False):
                valid_kernels.append(kernel)

        self.kernels = valid_kernels

    def find_kernels_with_fixes_subj(self, linux_sha):
        """Filters out kernels without fixes commit given through the linux sha."""
        valid_kernels = []

        fixes_sha = self.get_fixes_commit(linux_sha)

        if fixes_sha == '':
            self.logger.debug(f'Commit {linux_sha} does not have a Fixes tag')
            return

        subject = self.get_subject_line(fixes_sha)

        for kernel in self.kernels:
            self.logger.debug(f'Checking if {kernel} contains fixes commit: {fixes_sha}')

            kernel_path = os.path.join(os.getenv('CHROMIUMOS_KERNEL'), kernel)

            branch = common.get_cros_branch(kernel)
            common.checkout_branch(kernel, f'cros/{branch}', 'cros', branch, kernel_path)

            if self.is_in_kernel(kernel_path, subject, True):
                valid_kernels.append(kernel)

        self.kernels = valid_kernels

    def detect_relevant_commits(self, linux_sha):
        """Displays information about fixes that refer to the linux sha."""
        linux_subj = self.get_subject_line(linux_sha)

        shas = subprocess.check_output(['git', 'log', '--format=%H'],
                                       stderr=subprocess.DEVNULL, cwd=os.getenv('LINUX'),
                                       encoding='utf-8')

        sha_list = shas.split('\n')

        for sha in sha_list:
            if linux_sha in sha:
                break

            fixes_sha = self.get_fixes_commit(sha)

            if fixes_sha == '':
                continue

            try:
                fixes_subj = self.get_subject_line(fixes_sha)
            except ContextGeneratorException:
                # Given sha contains fixes tag from another working tree.
                # Ex: 1bb0fa189c6a is refered to by a7868323c2638a7c6c5b30b37831b73cbdf0dc15.
                self.logger.error(f'{sha} contains a fix commit from another working tree.')

            if fixes_subj == linux_subj:
                self.logger.info(f'Sha {sha} is a relevant commit.')
                self.relevant_commits.append(sha)
                return

    def generate_context(self, linux_sha):
        """Generates list of kernels with same commit as provided by linux_sha."""
        self.filter_fixed_kernels(linux_sha)

        self.find_kernels_with_fixes_subj(linux_sha)

        self.filter_based_on_stable(linux_sha, 'STABLE')

        self.filter_based_on_stable(linux_sha, 'STABLE_RC')

        if self.check_rel_commits:
            self.detect_relevant_commits(linux_sha)
