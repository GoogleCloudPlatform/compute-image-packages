#!/bin/bash
# Copyright 2018 Google Inc. All Rights Reserved.
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
OUTPUT="$(curl -f -H Metadata-Flavor:Google ${URL}/output_path)"

if [ -z $OUTPUT ]; then
  OUTPUT="$(curl -f -H Metadata-Flavor:Google ${URL}/daisy-outs-path)"
fi

if [[ ! -e /etc/redhat-release ]]; then
  echo "BuildFailed: not a RHEL host!"
  exit 1
fi

workdir=$(pwd)
mkdir output

sudo yum install -y git

# Clone the github repo.
git clone ${GIT_REPO} -b ${BRANCH} compute-image-packages
if [ $? -ne 0 ]; then
  echo "BuildFailed: Unable to clone github repo ${GIT_REPO} and branch ${BRANCH}"
  exit 1
fi

# Build packages.
cd compute-image-packages/packages
for package in *; do
  [[ -d "${package}/packaging" ]] || continue
  pushd "$package"
  ./packaging/setup_rpm.sh
  if [[ $? -ne 0 ]]; then
    echo "BuildFailed: Unable to build $package"
    exit 1
  fi
  find /tmp/rpmpackage -iname '*.rpm' -exec mv '{}' "${workdir}/output/" \;
  popd
done

# Copy the rpm files to the output.
cd "${workdir}/output"
gsutil cp *.rpm ${OUTPUT}
if [ $? -ne 0 ]; then
  echo "BuildFailed: copying to ${OUTPUT} failed."
  exit 1
fi

echo "BuildSuccess: Packages are in ${OUTPUT}."
