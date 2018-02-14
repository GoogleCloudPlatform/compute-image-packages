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

if [ -z ${OUTPUT} ]; then
  OUTPUT="$(curl -f -H Metadata-Flavor:Google ${URL}/daisy-outs-path)"
fi

# Install build dependencies.
yum -y install git rpmdevtools \
  python2-devel python-boto \
  make gcc-c++ libcurl-devel json-c json-c-devel pam-devel \
  policycoreutils-python

# Install python setuptools.
easy_install pip
pip install "setuptools>20.0.0"

# Clone the github repo.
git clone ${GIT_REPO} -b ${BRANCH}
if [ $? -ne 0 ]; then
  echo "BuildFailed: Unable to clone github repo ${GIT_REPO} and branch ${BRANCH}"
  exit 1
fi

# Create tar's for package builds.
tar -czvf google-compute-engine_${VERSION}.orig.tar.gz --exclude .git compute-image-packages

# Setup rpmbuild tree.
for d in BUILD BUILDROOT RPMS SOURCES SPECS SRPMS; do
  mkdir -p /rpmbuild/$d
done
cp compute-image-packages/specs/*.spec /rpmbuild/SPECS/
cp google-compute-engine_${VERSION}.orig.tar.gz /rpmbuild/SOURCES/

# Build the RPM's
for spec in $(ls /rpmbuild/SPECS/*.spec); do
 rpmbuild --define "_topdir /rpmbuild" -ba $spec
  if [ $? -ne 0 ]; then
    echo "BuildFailed: rpmbuild for $spec failed."
    exit 1
  fi
done

# Copy the rpm and srpms to the output.
gsutil cp /rpmbuild/RPMS/*/*.rpm /rpmbuild/SRPMS/*.src.rpm ${OUTPUT}/
if [ $? -ne 0 ]; then
  echo "BuildFailed: copying to ${OUTPUT} failed."
  exit 1
fi

echo "BuildSuccess: Packages are in ${OUTPUT}."
