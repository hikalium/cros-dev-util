#!/bin/bash
# Copyright 2021 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

set -e
script_dir="$(dirname "$(realpath -e "${BASH_SOURCE[0]}")")"
readonly script_dir

source "${script_dir}/../../../../../test/docker/util.sh"

build_server_image "testplan" "${script_dir}/Dockerfile" "$@"
