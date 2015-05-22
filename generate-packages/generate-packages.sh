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

if [ "$(id -u)" != "0" ]; then
  echo "Error: Requested operation requires superuser privilege." 1>&2
  exit 1
fi

sudo apt-get update
sudo apt-get install gcc ruby-dev rpm
sudo gem install fpm

RELEASE_VERSION=1.25
DEPENDENCIES="python"
ARCHITECTURE="all"
SOURCE_TYPE="dir"
SOURCE_DIR="compute-image-packages"

PACKAGE_NAME="compute-image"
LICENSE="Apache"
DESCRIPTION="Package for Google Compute Image."
MAINTAINER="bigcluster-accounts-eng@google.com"
URL="https://github.com/GoogleCloudPlatform/compute-image-packages"
VENDOR="Google Inc."

supported_packages=("deb" "rpm")
target_packages=()

while getopts "dhr" opt; do
  case "${opt}" in
  h|\?)
    echo "sudo ./generate_packages.sh [-deb | -rpm ]" 1>&2
    exit 1
    ;;
  d)
    target_packages=("${target_packages[@]}" "deb")
    ;;
  r)
    target_packages=("${target_packages[@]}" "rpm")
    ;;
  esac
done

if [ ${#target_packages[@]} -eq 0 ]; then
	target_packages=("${supported_packages[@]}")
fi

for target_package in "${target_packages[@]}"
do
  fpm -s "$SOURCE_TYPE" -t "$target_package" -v "$RELEASE_VERSION" -a "$ARCHITECTURE" --license "$LICENSE" -m "$MAINTAINER" --description "$DESCRIPTION" --url "$URL" --vendor "$VENDOR" -d "$DEPENDENCIES" --after-install ./"$target_package"-post-install.sh --before-remove ./"$target_package"-pre-remove.sh -n "$PACKAGE_NAME" -f --verbose -x .git -x .gitignore -x generate-packages  "$SOURCE_DIR"
done
