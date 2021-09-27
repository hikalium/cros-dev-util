#!/bin/bash
# Copyright 2021 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

set -e
readonly script_dir="$(dirname "$(realpath -e "${BASH_SOURCE[0]}")")"

source "${script_dir}/../../../../../test/docker/util.sh"

usage() {
    echo "Usage: $0 <chroot> <sysroot> [options] [key=value...]"
    echo
    echo "Build a docker container for the cros-provision service."
    echo
    echo "Args:"
    echo "  chroot  - Path to the ChromeOS chroot on the host system."
    echo "  sysroot - Path inside of the chroot to the board sysroot."
    echo "  labels  - Zero or more key=value strings to apply as labels to container."
    echo
    echo "Options:"
    echo "  --tags/-t - Comma separated list of tag names to apply to container"
    exit 1
}

if [[ $# -lt 3 ]]; then
    usage
fi

chroot="$1"; shift
shift # don't care about sysroot

tags=""
while [[ $# -gt 0 ]]; do
    case $1 in
        --tags|-t)
            tags="$2"
            shift
            shift
            ;;
        *)
            break
            ;;
    esac
done

build_server_image             \
    "provisionserver"          \
    "${script_dir}/Dockerfile" \
    "${chroot}"                \
    "${tags}"                  \
    "${@}"
