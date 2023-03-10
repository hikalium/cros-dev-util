#!/bin/bash

# Copyright 2020 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

# Scripts to search blocked words.
#
# Usage: search_blocked_words.sh [/path/to/word_list.txt]
#
# You can search the current directory for globally blocked words:
#
#   $ search_blocked_words.sh
#
# You can pass the project's unblocked_terms.txt to narrow the search scope:
#
#   $ search_blocked_words.sh ./unblocked_terms.txt

input_file=${1:-~/trunk/src/repohooks/blocked_terms.txt}
if [[ ! -r "${input_file}" ]]; then
  echo "Error: '${input_file}' not found."
  echo "This script is expected to run in CrOS SDK chroot."
  echo "Read repohooks/README.md for more information."
  exit 1
fi

all=$(git ls-tree -r --name-only HEAD)

# Create list of paths without symlinks.
paths=()
while IFS= read -r path; do
  [[ -L "${path}" ]] && continue
  paths+=("${path}")
done <<< "${all}"

# Create lists of dirs, files, symlinks. Must be basename and have no duplicate.
# We use xargs (instead of directly feeding to dirname or basename) to avoid
# exceeding argument size limit.
dirs=$(echo ${all} | xargs dirname | sort -u | xargs basename -a)
files=$(echo ${all} | xargs basename -a)

results=("reg_exp #lines #files #filenames")
while read -r regex; do
  # Skip blank and comment lines.
  [[ -z "${regex}" ]] && continue
  [[ "${regex}" == "#"* ]] && continue

  # Count matching lines.
  line_count=$(echo "${paths[@]}" | xargs grep -E -i -I -c "${regex}" \
      | awk -F: '{ s+=$2 } END { print s }')

  # Count matching paths.
  path_count=$(echo "${paths[@]}" | xargs grep -E -i -I -l "${regex}" | wc -l)

  # Count matching file & dir names.
  name_count=$(echo "${files}" "${dirs}" | grep -E -i "${regex}" | wc -l)

  # Save result.
  results+=("${regex} ${line_count} ${path_count} ${name_count}")
done < "${input_file}"

# Present results.
printf '%s\n' "${results[@]}" | column --table --table-right 2,3,4

