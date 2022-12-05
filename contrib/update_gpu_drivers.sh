#!/bin/bash
# Copyright 2015 The ChromiumOS Authors
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
DEFINE_string board "" \
  "selects which board to build on. Empty to build on all supported boards."
DEFINE_boolean dryrun "${FLAGS_FALSE}" \
  "dry run, don't upload anything and don't delete temporary dirs" n
DEFINE_boolean usebinpkg "${FLAGS_TRUE}" \
  "use prebuilt binaries, instead of building driver locally" b
DEFINE_boolean clobber "${FLAGS_FALSE}" \
  "overwrites the existing binaries when uploading" c

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
DRIVERS="arc-mali-drivers-bifrost arc-mali-drivers-valhall mali-drivers mali-drivers-bifrost mali-drivers-valhall img-ddk"

# List of parameters to pass to build_board, for a given package $pn:
#  - Build board names.
#  - Suffixes for tarball name.
#  - Overlay paths for each board.
#
# Variable name: "PARAMS_${pn//-/_}"

# Only add board that is still using ARC++ P
# shellcheck disable=SC2034
PARAMS_arc_mali_drivers_bifrost=(
  "kukui kukui chipset-mt8183"
)

# Only add board that is still using ARC++ P
# shellcheck disable=SC2034
PARAMS_arc_mali_drivers_valhall=(
  "asurada asurada chipset-mt8192"
  "cherry cherry chipset-mt8195"
)

# shellcheck disable=SC2034
PARAMS_mali_drivers=(
  "kevin gru baseboard-gru"
)

# shellcheck disable=SC2034
PARAMS_mali_drivers_bifrost=(
  "kukui kukui chipset-mt8183"
  "corsola corsola chipset-mt8186"
)

# shellcheck disable=SC2034
PARAMS_mali_drivers_valhall=(
  "asurada asurada chipset-mt8192"
  "cherry cherry chipset-mt8195"
  "geralt geralt chipset-mt8188g"
)

# shellcheck disable=SC2034
PARAMS_img_ddk=(
  "elm oak chipset-mt8173"
)

create_run_script() {
  local script="$1"
  local outputtarball="$2"
  local hdrsize

  cat > "${script}" <<\__HDREOF__
#!/bin/sh
#
# Copyright 2015 The ChromiumOS Authors
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

  {
    cat "${SRC_ROOT}/third_party/chromiumos-overlay/licenses/Google-TOS"
    echo __EOF__
  } >> "${script}"

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

  hdrsize=$(wc -l < "${script}")

  sed -i "s/@HDRSZ@/$(( hdrsize + 1 ))/g" "${script}"

  cat "${outputtarball}" >> "${script}"

  chmod +x "${script}"
  du -b "${script}"
}

commit_change() {
  git commit --edit -m "$(cat <<EOM
${opath}: ${pnbin}: Uprev to ${pv}

Via ~/chromiumos/src/platform/dev/contrib/update_gpu_drivers.sh
      --package ${pn}

BUG=TODO
TEST=emerge-${board} -av ${pnbin}
EOM
)"
}

# arguments:
# $1 board name (Chrome OS board name to build)
# $2 binary package suffix (suffix added to tar package name)
# $3 overlay path

build_board() {
  local board=$1
  local suffix=$2
  local opath=$3
  info "Board is ${board}"

  # Source PVR (e.g. 13.0-r6)
  local pvr
  local inputtarball

  local temp="${TEMP_DIR}/${suffix}"
  mkdir "${temp}"
  pushd "${temp}" > /dev/null || die "Couldn't pushd ${temp}."

  if [[ ${FLAGS_usebinpkg} -eq ${FLAGS_TRUE} ]]; then
    # Fetch binary package from Google Storage.
    local partner_overlay="${SRC_ROOT}/private-overlays/chromeos-partner-overlay"
    local binhost_gs
    local packages_file
    local prebuilt_path

    # Fetch latest preflight prebuilt version.
    git --git-dir "${partner_overlay}/.git" fetch --all
    binhost_gs="$(git --git-dir "${partner_overlay}/.git" show \
                  "m/main:chromeos/binhost/target/${board}-POSTSUBMIT_BINHOST.conf" | \
                  sed -nE 's/POSTSUBMIT_BINHOST=\"(.*)\"/\1/p' | \
                  cut -d' ' -f1)"

    # Parse Packages file to find GS path of the latest ${pn} prebuilt.
    packages_file="$(gsutil cat "${binhost_gs}/Packages")"
    prebuilt_path="$(echo "${packages_file}" | \
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

    if ! setup_board --board="${board}"; then
      die "Setting up board ${board} failed."
    fi

    # Make sure we are not building -9999 ebuild.
    # This could fail if cros_workon is already stopped so ignore return code.
    cros_workon --board="${board}" stop "${pn}"

    if ! "emerge-${board}" "${pn}"; then
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

  info "Current version is ${pvr}"
  info "Input tarball is ${inputtarball}"
  info "Output tarball is ${outputtarball}"
  info "Script is ${script}"

  if ! mkdir work; then
    die "Couldn't create work directory."
  fi

  if ! qtbz2 -tO "${inputtarball}" | tar -C work --zstd -xpv; then
    die "Couldn't decompress package tarball ${inputtarball}."
  fi

  if ! tar -C work --exclude=usr/lib/debug -cpjvf "${outputtarball}" ./; then
    die "Couldn't create ${outputtarball}."
  fi

  create_run_script "${script}" "${outputtarball}"

  info "Uploading tarball to ${gspath}/${script}"
  if [[ ${FLAGS_dryrun} -eq ${FLAGS_TRUE} ]]; then
    info "Would run: gsutil cp -n -a public-read \"${script}\" \"${gspath}/${script}\""
  else
    local extra_args=()

    if [[ ${FLAGS_clobber} -eq ${FLAGS_FALSE} ]]; then
      if gsutil ls -a "${gspath}/${script}" 2>/dev/null; then
        warn "${gspath}/${script} exists."
        warn "Retry with -c or --clobber to overwrite the existing binaries."
        exit 1
      fi
      extra_arg+=( "-n" )
    fi

    if ! gsutil cp "${extra_args[@]}" -a public-read "${script}" "${gspath}/${script}"; then
      die "Couldn't upload ${script} to ${gspath}/${script}."
    fi
  fi

  # Uprev ebuild in git if it exists.
  local pnbin_path="${SRC_ROOT}/overlays/${opath}/${CATEGORY}/${pnbin}"
  if [[ -d "${pnbin_path}" ]]; then
    cd "${pnbin_path}" || die "Couldn't cd to ${pnbin_path}."

    # Grab the version of the current release of the binary package.
    local pvbin
    pvbin="$(printf '%s\n' *.ebuild | \
             sed -nE "s/^${pnbin}-(.*)\.ebuild\$/\1/p" | \
             sort -V | tail -n 1)"
    info "New binary version: ${pv} (current binary version: ${pvbin})"

    # following git commands may fail if they have been issued previously
    git checkout -b "gpudriverbinupdate-${pnbin}-${pv}"
    git mv "${pnbin}-${pvbin}.ebuild" "${pnbin}-${pv}.ebuild"

    if ! ebuild "${pnbin}-${pv}.ebuild" manifest; then
      die "Couldn't update manifest for ${pnbin}-${pv}."
    fi

    if ! git add "Manifest"; then
      die "Couldn't git add Manifest."
    fi

    if ! commit_change; then
      warn "The changes are not commited."
    fi
  else
    warn "${pnbin_path} doesn't exist."
    warn "Please create the package and the base ebuild file."
  fi

  popd > /dev/null || die "Couldn't popd."
}

cleanup() {
  trap - INT TERM ERR EXIT

  if [[ ${FLAGS_dryrun} -eq ${FLAGS_FALSE} ]]; then
    rm -rf "${TEMP_DIR}"
  fi
}

main() {
  if [[ -z ${FLAGS_package} ]]; then
    die "Please select a package using --package [${DRIVERS// /|}]"
  fi

  local params
  local typed

  trap cleanup INT TERM ERR EXIT

  info "$(basename "$0") builds GPU drivers for a list of boards."
  info 'It uploads the binaries to Google storage and generates corresponding'
  info 'commits for submission.'
  info 'It makes the pre-built GPU binaries available in the public repository'
  info 'for external partners and developers to use.'
  info 'It expects you have configured gsutil.'
  info

  if [[ ${FLAGS_dryrun} -eq ${FLAGS_TRUE} ]]; then
    info "Running with --dryrun, moving forward."
  else
    printf 'Type "y" if you know what you are doing and want to go ahead: '
    read -r typed

    if [[ "${typed}" != y ]]; then
      info
      info "Good choice."
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
    warn
    warn "Nothing to do for ${pn}, you probably chose an incorrect package name."
    warn "Supported packages: ${DRIVERS}"
    exit 1
  fi

  TEMP_DIR="$(mktemp -d)"
  info "Temp dir is ${TEMP_DIR}"

  local found=0
  local boards=()
  for params in "${!array}"; do
    # shellcheck disable=SC2206   # Expand on whitespace.
    params=( ${params} )
    board="${params[0]}"
    boards+=( "${board}" )

    if [[ -z "${FLAGS_board}" || "${FLAGS_board}" == "${board}" ]]; then
      found=1
      build_board "${params[@]}"
    fi
  done

  if [[ ${found} -eq 0 ]]; then
    warn "Nothing to do for board '${FLAGS_board}'."
    warn "${pn} supports following boards: ${boards[*]}"
  fi
}

main "$@"
