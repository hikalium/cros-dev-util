# Copyright (c) 2012 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

all: devserver

devserver:
	@echo "Preparing devserver modules."

install:
	mkdir -p "${DESTDIR}/usr/bin"
	mkdir -p "${DESTDIR}/usr/lib/devserver"
	mkdir -p "${DESTDIR}/usr/lib/devserver/dut-scripts"
	install -m 0755 host/start_devserver "${DESTDIR}/usr/bin"
	install -m 0755 devserver.py strip_package.py "${DESTDIR}/usr/lib/devserver"
	install -m 0644  \
		android_build.py \
		artifact_info.py \
		autoupdate.py \
		build_artifact.py \
		build_util.py \
		builder.py \
		cherrypy_ext.py \
		common_util.py \
		cros_update.py \
		cros_update_logging.py \
		cros_update_progress.py \
		devserver_constants.py \
		downloader.py \
		health_checker.py \
		log_util.py \
		nebraska/nebraska.py \
		retry.py \
		setup_chromite.py \
		xbuddy.py \
		xbuddy_config.ini\
		"${DESTDIR}/usr/lib/devserver"

	install -m 0755 stateful_update "${DESTDIR}/usr/bin"

	# The content in /var/lib is only meaningful for installation in
	# a chroot, not for Moblab.
	mkdir -m0777 -p "${DESTDIR}/var/lib/devserver"
	mkdir -m0777 -p "${DESTDIR}/var/lib/devserver/static"
	mkdir -m0777 -p "${DESTDIR}/var/lib/devserver/static/cache"

	# The dut-scripts content is only used when installed on Moblab.
	# Mode 0644 for these files because they're for serving to DUTs
	# over HTTP, not for local execution.
	install -m 0644 stateful_update \
		"${DESTDIR}/usr/lib/devserver/dut-scripts"
	install -m 0644 quick-provision/quick-provision \
		"${DESTDIR}/usr/lib/devserver/dut-scripts"

.PHONY: all devserver install
