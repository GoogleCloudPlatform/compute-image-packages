#!/bin/bash
# Copyright 2017 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

URL="http://metadata/computeMetadata/v1/instance/attributes"
BRANCH="$(curl -f -H Metadata-Flavor:Google ${URL}/github_branch)"
GIT_REPO="$(curl -f -H Metadata-Flavor:Google ${URL}/github_repo)"
VERSION="$(curl -f -H Metadata-Flavor:Google ${URL}/package_version)"
OUTPUT="$(curl -f -H Metadata-Flavor:Google ${URL}/output_path)"
DEB_VER="$(cut -d "." -f 1 /etc/debian_version)"

if [ -z ${OUTPUT} ]; then
  OUTPUT="$(curl -f -H Metadata-Flavor:Google ${URL}/daisy-outs-path)"
fi

# Install build dependencies.
apt-get update
apt-get -y install git debhelper devscripts dh-python dh-systemd \
  python-all python-boto python-setuptools python-pytest python-mock \
  python3-all python3-boto python3-setuptools python3-pytest python3-mock \
  python3-distro \
  libcurl4-openssl-dev libjson-c-dev libpam-dev build-essential
if [ $? -ne 0 ]; then
  echo "BuildFailed: Unable to install build dependencies."
  exit 1
fi

# Clone the github repo.
git clone ${GIT_REPO} -b ${BRANCH}
if [ $? -ne 0 ]; then
  echo "BuildFailed: Unable to clone github repo ${GIT_REPO} and branch ${BRANCH}"
  exit 1
fi

# Create tar's for package builds.
tar -czvf google-compute-image-packages_${VERSION}.orig.tar.gz --exclude .git compute-image-packages

# Build the deb's
pushd compute-image-packages
debuild -us -uc
if [ $? -ne 0 ]; then
  echo "BuildFailed: debuild failed."
  exit 1
fi
popd

# Copy the deb and dsc files to the output.
gsutil cp *.dsc *.deb ${OUTPUT}/
if [ $? -ne 0 ]; then
  echo "BuildFailed: copying to ${OUTPUT} failed."
  exit 1
fi

echo "BuildSuccess: Packages are in ${OUTPUT}."
