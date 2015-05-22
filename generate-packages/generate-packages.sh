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

RELEASE_VERSION=1.25
DEPENDENCIES="python"
ARCHITECTURE="all"
SOURCE_TYPE="dir"

PACKAGE_NAME="compute-image"
LICENSE="Apache"
DESCRIPTION="Package for Google Compute Image."
MAINTAINER="bigcluster-accounts-eng@google.com"
URL="https://github.com/GoogleCloudPlatform/compute-image-packages"
VENDOR="Google Inc."

SOURCES=" \
  gcimagebundle=/compute-image-packages \
  google-daemon/etc=/ \
  google-daemon/usr=/ \
  google-startup-scripts/lib=/ \
  google-startup-scripts/etc=/ \
  google-startup-scripts/usr=/"

generate_deb=true
generate_rpm=true

while getopts "dhr" opt; do
  case "${opt}" in
  h|\?)
    echo "./generate_packages.sh [-d | -r ]" 1>&2
    exit 1
    ;;
  d)
    generate_rpm=false
    ;;
  r)
    generate_deb=false
    ;;
  esac
done

if  $generate_deb ; then
	fpm -s "$SOURCE_TYPE" -t "deb" -v "$RELEASE_VERSION" -a "$ARCHITECTURE" --license "$LICENSE" -m "$MAINTAINER" --description "$DESCRIPTION" --url "$URL" --vendor "$VENDOR" -d "$DEPENDENCIES" -C .. --after-install deb-post-install.sh --before-remove deb-pre-remove.sh -n "$PACKAGE_NAME" -f --verbose $SOURCES
fi

if  $generate_rpm ; then
  fpm -s "$SOURCE_TYPE" -t "rpm" -v "$RELEASE_VERSION" -a "$ARCHITECTURE" --license "$LICENSE" -m "$MAINTAINER" --description "$DESCRIPTION" --url "$URL" --vendor "$VENDOR" -d "$DEPENDENCIES" -C .. --after-install rpm-post-install.sh --before-remove rpm-pre-remove.sh -n "$PACKAGE_NAME" -f --verbose -x **etc/rc.local $SOURCES
fi
