#!/bin/bash
# Copyright 2015 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

# This script builds gpu drivers (mali-drivers[-*], img-ddk) for a list
# of boards. It uploads the binaries to Google storage and makes them available
# in the public repository.

# Loads script libraries.
CONTRIB_DIR=$(dirname "$(readlink -f "$0")")
. "${CONTRIB_DIR}/common.sh" || exit 1

DEFINE_string package "" \
  "selects which gpu drivers package to build"
DEFINE_boolean dryrun ${FLAGS_FALSE} \
  "dry run, don't upload anything and don't delete temporary dirs" n
DEFINE_boolean usebinpkg ${FLAGS_TRUE} \
  "use prebuilt binaries, instead of building driver locally" b

# Parse command line.
FLAGS "$@" || exit 1
eval set -- "${FLAGS_ARGV}"

# Script must run inside the chroot.
assert_inside_chroot

# The temp dir to use for scratch space.
TEMP_DIR=""

# All drivers are in media-libs/ portage category.
CATEGORY="media-libs"
# List of supported drivers
DRIVERS="mali-drivers mali-drivers-bifrost mali-drivers-valhall img-ddk"

# List of parameters to pass to build_board, for a given package $pn:
#  - Build board names.
#  - Suffixes for tarball name.
#  - Overlay paths for each board.
#
# Variable name: "PARAMS_${pn//-/_}"

PARAMS_mali_drivers=(
  "daisy daisy overlay-daisy"
  "kevin gru baseboard-gru"
  "peach_pit peach overlay-peach"
  "veyron_jerry veyron overlay-veyron"
)

PARAMS_mali_drivers_bifrost=(
  "kukui kukui chipset-mt8183"
)

PARAMS_mali_drivers_valhall=(
  "asurada asurada chipset-mt8192"
)

PARAMS_img_ddk=(
  "elm oak chipset-mt8173"
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
# $3 overlay path

build_board() {
  local board=$1
  local suffix=$2
  local opath=$3
  echo "Board is ${board}"

  # Source PVR (e.g. 13.0-r6)
  local pvr
  local inputtarball

  local temp="${TEMP_DIR}/${suffix}"
  mkdir "${temp}"
  pushd "${temp}" > /dev/null

  if [[ ${FLAGS_usebinpkg} -eq ${FLAGS_TRUE} ]]; then
    # Fetch binary package from Google Storage.
    local partner_overlay="${SRC_ROOT}/private-overlays/chromeos-partner-overlay"

    # Fetch latest preflight prebuilt version.
    git --git-dir "${partner_overlay}/.git" fetch --all
    local binhost_gs="$(git --git-dir "${partner_overlay}/.git" show \
        "m/master:chromeos/binhost/target/${board}-POSTSUBMIT_BINHOST.conf" | \
      sed -nE 's/POSTSUBMIT_BINHOST=\"(.*)\"/\1/p')"

    # Parse Packages file to find GS path of the latest ${pn} prebuilt.
    local prebuilt_path="$(gsutil cat "${binhost_gs}/Packages" | \
      awk '
        $1 == "CPV:" && $2 ~ /'"${CATEGORY}"'\/'"${pn}"'-[0-9]/ { m = 1 }
        m && $1 == "PATH:" { print $2 }
        m && $1 == "" { exit }
      ')"
    local package_gs="gs://chromeos-prebuilt/${prebuilt_path}"

    gsutil cp "${package_gs}" .

    inputtarball="${temp}/${package_gs##*/}"
    pvr="${package_gs%.*}"
    pvr="${pvr##*${pn}-}"
  else
    # Build from source.
    setup_board --board="${board}"
    if [[ $? != 0 ]]; then
      die "Setting up board ${board} failed."
    fi

    # Make sure we are not building -9999 ebuild.
    # This could fail if cros_workon is already stopped so ignore return code.
    cros_workon --board="${board}" stop "${pn}"

    "emerge-${board}" "${pn}"

    if [[ $? != 0 ]]; then
      die "Emerging ${pn} for ${board} failed."
    fi

    pvr="$("equery-${board}" -q list -p -o --format="\$fullversion" "${pn}" | \
           sort -V | head -n 1)"
    inputtarball="/build/${board}/packages/${CATEGORY}/${pn}-${pvr}.tbz2"
  fi

  # Binary PV (e.g. 13.0_p6)
  local pv="${pvr/-r/_p}"
  local outputtarball="${pn}-${suffix}-${pv}.tbz2"
  local script="${pn}-${suffix}-${pv}.run"
  local gspath="gs://chromeos-localmirror/distfiles"

  echo "Current version is ${pvr}"
  echo "Input tarball is ${inputtarball}"
  echo "Output tarball is ${outputtarball}"
  echo "Script is ${script}"

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
  fi

  # Uprev ebuild in git if it exists.
  if [[ -d "${SRC_ROOT}/overlays/${opath}/${CATEGORY}/${pnbin}" ]]; then
    cd "${SRC_ROOT}/overlays/${opath}/${CATEGORY}/${pnbin}"

    # Grab the version of the current release of the binary package.
    local pvbin="$(printf '%s\n' *.ebuild | \
                   sed -nE "s/^${pnbin}-(.*)\.ebuild\$/\1/p" | \
                   sort -V | tail -n 1)"
    echo "New binary version: ${pv} (current binary version: ${pvbin})"

    # following git commands may fail if they have been issued previously
    git checkout -b "gpudriverbinupdate-${pnbin}-${pv}"
    git mv "${pnbin}-${pvbin}.ebuild" "${pnbin}-${pv}.ebuild"

    ebuild "${pnbin}-${pv}.ebuild" manifest
  fi

  popd > /dev/null
}

cleanup() {
  trap - INT TERM ERR EXIT

  rm -rf "${TEMP_DIR}"
}

main() {
  if [[ -z ${FLAGS_package} ]]; then
    die "Please select a package using --package [${DRIVERS// /|}]"
  fi

  local params
  local typed

  trap cleanup INT TERM ERR EXIT

  echo 'This script builds gpu drivers for a list of boards. It uploads the'
  echo 'binaries to Google storage and makes them available in the public'
  echo 'repository. It expects you have configured gsutil.'
  echo

  if [[ ${FLAGS_dryrun} -eq ${FLAGS_TRUE} ]]; then
    echo "Running with --dryrun, moving forward."
  else
    printf 'Type "y" if you know what you are doing and want to go ahead: '
    read typed

    if [[ "${typed}" != y ]]; then
      echo
      echo "Good choice."
      exit 2
    fi
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

  TEMP_DIR="$(mktemp -d)"
  echo "Temp dir is ${TEMP_DIR}"

  for params in "${!array}"; do
    build_board ${params}
  done
}

main "$@"
