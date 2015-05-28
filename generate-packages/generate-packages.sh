#!/bin/bash
# Copyright 2015 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

set -o pipefail
set -e

RELEASE_VERSION=1.2.5
DEPENDENCIES="python"
ARCHITECTURE="all"
SOURCE_TYPE="dir"

PACKAGE_NAME="compute-image"
LICENSE="Apache"
DESCRIPTION="Package for Google Compute Image."
MAINTAINER="bigcluster-accounts-eng@google.com"
URL="https://github.com/GoogleCloudPlatform/compute-image-packages"
VENDOR="Google Inc."

SOURCES="\
  gcimagebundle=/compute-image-packages \
  google-daemon/etc=/ \
  google-daemon/usr=/ \
  google-startup-scripts/lib=/ \
  google-startup-scripts/etc=/ \
  google-startup-scripts/usr=/"

CONFIG_FILES_ARGS="\
  --config-files /etc/init/google-accounts-manager-service.conf \
  --config-files /etc/init/google-accounts-manager-task.conf \
  --config-files /etc/init/google-address-manager.conf \
  --config-files /etc/init/google-clock-sync-manager.conf \
  --config-files /etc/init/google.conf \
  --config-files /etc/init/google_run_shutdown_scripts.conf \
  --config-files /etc/init/google_run_startup_scripts.conf \
  --config-files /etc/rsyslog.d/90-google.conf \
  --config-files /etc/sysctl.d/11-gce-network-security.conf"


DEB_ARGS=" -t deb --before-install deb-pre-install.sh --after-install deb-post-install.sh --after-remove deb-post-remove.sh"
RPM_ARGS=" -t rpm --before-install rpm-pre-install.sh --after-install rpm-post-install.sh --before-remove rpm-pre-remove.sh --after-remove rpm-post-remove.sh"

GENERATE_COMMAND="fpm -s ${SOURCE_TYPE} -v '${RELEASE_VERSION}' -a '${ARCHITECTURE}' --license '${LICENSE}' -m '${MAINTAINER}' --description '${DESCRIPTION}' --url '${URL}' --vendor '${VENDOR}' -d ${DEPENDENCIES} -C .. -n '${PACKAGE_NAME}' -f --verbose -x **etc/rc.local ${CONFIG_FILES_ARGS}"

# Generate Deb Package
eval ${GENERATE_COMMAND} ${DEB_ARGS} ${SOURCES}

# Generate RPM Package
eval ${GENERATE_COMMAND} ${RPM_ARGS} ${SOURCES}
