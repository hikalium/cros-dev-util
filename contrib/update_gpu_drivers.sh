#!/bin/bash
# Copyright 2015 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

# This script builds gpu drivers (mali-drivers[-bifrost], img-ddk) for a list
# of boards. It uploads the binaries to Google storage and makes them available
# in the public repository.

# Loads script libraries.
CONTRIB_DIR=$(dirname "$(readlink -f "$0")")
. "${CONTRIB_DIR}/common.sh" || exit 1

DEFINE_string package "" \
  "selects which gpu drivers package to build"
DEFINE_boolean dryrun ${FLAGS_FALSE} \
  "dry run, don't upload anything and don't delete temporary dirs" n

# Parse command line.
FLAGS "$@" || exit 1
eval set -- "${FLAGS_ARGV}"

# Script must run inside the chroot.
assert_inside_chroot

# List of supported drivers
DRIVERS="mali-drivers mali-drivers-bifrost img-ddk"

# List of parameters to pass to build_board, for a given package $pn:
#  - Build board names.
#  - Suffixes for tarball name.
#  - Board names for overlay with mali-drivers-bin.ebuild.
#  - Overlay paths for each board.
#
# Variable name: "PARAMS_${pn//-/_}"

PARAMS_mali_drivers=(
  "daisy daisy daisy overlay-daisy"
  "kevin gru gru baseboard-gru"
  "peach_pit peach peach overlay-peach"
  "veyron_jerry veyron veyron overlay-veyron"
)

PARAMS_mali_drivers_bifrost=(
  "kukui kukui kukui chipset-mt8183"
)

PARAMS_img_ddk=(
  "elm oak oak chipset-mt8173"
)

create_run_script() {
  local script="$1"
  local outputtarball="$2"

  cat > "${script}" <<\__HDREOF__
#!/bin/sh
#
# Copyright 2015 The Chromium OS Authors. All rights reserved.
#
# Usage is subject to the enclosed license agreement.
# To be generated by Makeself 1.5.3
skip=@HDRSZ@
echo
echo The license for this software will now be displayed.
echo You must agree to this license before using this software.
echo

more << __EOF__
__HDREOF__

  cat "${SRC_ROOT}/third_party/chromiumos-overlay/licenses/Google-TOS" >> "${script}"
  echo __EOF__ >> "${script}"
  cat >> "${script}" <<\__BODYEOF__
if [ $? != 0 ]; then
  echo "ERROR: Couldn't display license file" 1>&2
  exit 1
fi

echo

printf 'Type "y" if you agree to the terms of the license: '
read typed

if [ "${typed}" != y ]; then
  echo
  echo "You didn't accept the license. Extraction aborted."
  exit 2
fi

echo

tail -n +${skip} "$0" | tar xjv 2>/dev/null

if [ $? -ne 0 ]; then
  echo
  echo "ERROR: Couldn't extract files." 1>&2
  exit 3
else
  echo
  echo "Files extracted successfully."
fi
exit 0
__BODYEOF__

  local hdrsize=$(wc -l < "${script}")

  sed -i "s/@HDRSZ@/$(( hdrsize + 1 ))/g" "${script}"

  cat "${outputtarball}" >> "${script}"

  chmod +x "${script}"
  du -b "${script}"
}

# arguments:
# $1 board name (Chrome OS board name to build)
# $2 binary package suffix (suffix added to tar package name)
# $3 overlay board name
# $4 overlay path

build_board() {
  local board=$1
  local suffix=$2
  local oboard=$3
  local opath=$4
  echo "Board is ${board}"

  if [[ "$oboard" != "X11" ]]; then
    "${SRC_ROOT}/scripts/setup_board" --board="${oboard}"
  fi
  "${SRC_ROOT}/scripts/setup_board" --board="${board}"
  if [[ $? != 0 ]]; then
    die "Setting up board ${board} failed."
  fi

  # Make sure we are not building -9999 ebuild.
  # This could fail if cros_workon is already stopped so ignore return code.
  cros_workon --board="${board}" stop ${pn}

  if [[ "$oboard" == "X11" ]]; then
    echo "Building special X11 package"
    USE=X emerge-${board} ${pn}
  else
    emerge-${board} ${pn}
  fi

  if [[ $? != 0 ]]; then
    die "Emerging ${pn} for ${board} failed."
  fi

  local pv=$("equery-${board}" -q list -p -o --format="\$fullversion" ${pn} | sort | head -n 1)
  local category=$("equery-${board}" -q list -p -o --format="\$category" ${pn} | sort | head -n 1)
  local inputtarball="/build/${board}/packages/${category}/${pn}-${pv}.tbz2"
  local outputtarball="${pn}-${suffix}-${pv}.tbz2"
  local script="${pn}-${suffix}-${pv}.run"
  local gspath="gs://chromeos-localmirror/distfiles"

  echo "Current version is ${pv}"
  echo "Input tarball is ${inputtarball}"
  echo "Output tarball is ${outputtarball}"
  echo "Script is ${script}"

  local temp=$(mktemp -d)
  echo "Temp dir is ${temp}"
  pushd "${temp}" >& /dev/null

  mkdir work
  if [[ $? != 0 ]]; then
    die "Couldn't create work directory."
  fi

  tar -C work -xpjvf "${inputtarball}"
  if [[ $? != 0 ]]; then
    die "Couldn't decompress package tarball ${inputtarball}."
  fi

  tar -C work --exclude=usr/lib/debug -cpjvf "${outputtarball}" ./
  if [[ $? != 0 ]]; then
    die "Couldn't create ${outputtarball}."
  fi

  create_run_script "${script}" "${outputtarball}"

  echo "Uploading tarball to ${gspath}/${script}"
  if [[ ${FLAGS_dryrun} -eq ${FLAGS_TRUE} ]]; then
    echo "Would run: gsutil cp -a public-read \"${script}\" \"${gspath}/${script}\""
  else
    gsutil cp -a public-read "${script}" "${gspath}/${script}"
    if [[ $? != 0 ]]; then
      die "Couldn't upload ${script} to ${gspath}/${script}."
    fi
    rm -rf "${temp}"
  fi

  if [[ "${oboard}" != "X11" ]]; then
    local pvbin=$("equery-${board}" -q list -p -o --format="\$fullversion" ${pnbin} | sort | head -n 1)
    echo "Current version is ${pv} current binary version is ${pvbin}"
    # Uprev ebuild in git if it exists.
    if [[ -d "${SRC_ROOT}/overlays/${opath}/${category}/${pnbin}" ]]; then
      cd "${SRC_ROOT}/overlays/${opath}/${category}/${pnbin}"

      # following git commands may fail if they have been issued previously
      git checkout -b "gpudriverbinupdate-${pv}" m/master
      git mv "${pnbin}-${pvbin}.ebuild" "${pnbin}-${pv}.ebuild"

      "ebuild-${oboard}" "${pnbin}-${pv}.ebuild" manifest
    fi
  fi

  popd >& /dev/null
}

main() {
  if [[ -z ${FLAGS_package} ]]; then
    die "Please select a package using --package [${DRIVERS// /|}]"
  fi

  local params
  local typed
  echo 'This script builds gpu drivers for a list of boards. It uploads the'
  echo 'binaries to Google storage and makes them available in the public'
  echo 'repository. It expects you have configured gsutil.'
  echo

  printf 'Type "y" if you know what you are doing and want to go ahead: '
  read typed

  if [[ "${typed}" != y ]]; then
    echo
    echo "Good choice."
    exit 2
  fi

  if [[ ! -f "${HOME}/.boto" ]]; then
    die "You did not configure gsutil after all."
  fi

  local pn="${FLAGS_package}"
  local pnbin="${pn}-bin"

  local array="PARAMS_${pn//-/_}[@]"

  if [[ -z "${!array}" ]]; then
    echo
    echo "Nothing to do for ${pn}, you probably chose an incorrect package name."
    echo "Supported packages: ${DRIVERS}"
    exit 1
  fi

  for params in "${!array}"; do
    build_board ${params}
  done
}

main "$@"