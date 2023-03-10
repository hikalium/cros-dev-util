# -*- coding: utf-8 -*-
"""Define steps, package names, and directories for creating an Ambassador variant

Copyright 2020 The Chromium OS Authors. All rights reserved.
Use of this source code is governed by a BSD-style license that can be
found in the LICENSE file.
"""

from __future__ import print_function
import step_names

# Name of the baseboard
base = 'ambassador'

# Name of the baseboard in coreboot; usually the same but not always
coreboot_base = 'hatch'

# Name of the creboot reference board; usually the same but not always
coreboot_reference = 'puff'

# List of steps (named in step_names.py) to run in sequence to create
# the new variant of the baseboard
step_list = [
    step_names.PROJECT_CONFIG,
    step_names.FW_BUILD_CONFIG,
    step_names.CB_VARIANT,
    step_names.CB_CONFIG,
    step_names.ADD_FIT,
    step_names.GEN_FIT,
    step_names.COMMIT_FIT,
    step_names.EMERGE,
    step_names.PUSH,
    step_names.UPLOAD,
    step_names.FIND,
    step_names.CALC_CQ_DEPEND,
    step_names.ADD_CQ_DEPEND,
    step_names.RE_UPLOAD,
    step_names.CLEAN_UP]

# Base directory for coreboot
coreboot_dir = 'third_party/coreboot'

# Base directory for coreboot configs (None=use default)
cb_config_dir = None

# Package name for FSP
fsp = 'intel-cmlfsp'

# Package name for the fitimage
fitimage_pkg = 'coreboot-private-files-puff'

# Directory for fitimage; append '~/trunk/src/'' in chroot, '~/chromiumos/src' outside
# Ambassador firmware is comingled with Puff's, so fitimage goes there.
fitimage_dir = 'private-overlays/baseboard-puff-private/sys-boot/coreboot-private-files-puff'

# Directory under fitimage_dir where gen_fit_image.sh leaves its outputs
fitimage_outputs_dir = 'asset_generation/outputs'

# Explanation of gen_fit_image command
fitimage_cmd = './gen_fit_image.sh %s <path_to_fit_kit> -b'

# List of packages to cros_workon
workon_pkgs = [
    'coreboot', 'libpayload', 'vboot_reference', 'depthcharge', fsp,
    fitimage_pkg, 'chromeos-ec', 'chromeos-config-bsp-ambassador-private']

# The emerge command
emerge_cmd = 'emerge-ambassador'

# List of packages to emerge
emerge_pkgs = [
    'coreboot', 'libpayload', 'vboot_reference', 'depthcharge', fsp,
    fitimage_pkg, 'chromeos-ec', 'chromeos-config-bsp-ambassador-private',
    'chromeos-config', 'chromeos-config-bsp', 'coreboot-private-files',
    'chromeos-bootimage']

# List of packages to cros_workon to build the project config
config_workon_pkgs = ['chromeos-config-bsp-ambassador-private']

# List of packages to emerge to build the project config
config_emerge_pkgs = ['chromeos-config-bsp-ambassador-private']

# Directory for the private yaml file
# None; ambassador doesn't use model.yaml
private_yaml_dir = None

# List of commits that will be uploaded with `repo upload`
repo_upload_list = [
    step_names.CB_CONFIG, step_names.COMMIT_FIT,
    step_names.FW_BUILD_CONFIG]

# List of commits that will be pushed to review.coreboot.org
coreboot_push_list = [step_names.CB_VARIANT]

# List of steps that depend on other steps, and what those are.
# This list gets used for setting up Cq-Depend on the uploaded CLs.
depends = {
    step_names.CB_CONFIG: [step_names.FIND],
    step_names.FW_BUILD_CONFIG: [
        step_names.FIND, step_names.CB_CONFIG, step_names.COMMIT_FIT]
}
