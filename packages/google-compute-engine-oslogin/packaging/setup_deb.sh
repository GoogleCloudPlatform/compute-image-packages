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

NAME="google-compute-engine-oslogin"
VERSION="1.5.3"

DEB=$(cut -d. -f1 </etc/debian_version)
if [[ -z $DEB ]]; then
  echo "Can't determine debian version of build host"
  exit 1
fi

working_dir=${PWD}
if [[ $(basename "$working_dir") != $NAME ]]; then
  echo "Packaging scripts must be run from top of package dir."
  exit 1
fi

# Build dependencies.
echo "Installing dependencies."
sudo apt-get -y install make g++ libcurl4-openssl-dev libjson-c-dev libpam-dev \
  debhelper devscripts build-essential >/dev/null

rm -rf /tmp/debpackage
mkdir /tmp/debpackage
tar czvf /tmp/debpackage/${NAME}_${VERSION}.orig.tar.gz  --exclude .git \
  --exclude packaging --transform "s/^\./${NAME}-${VERSION}/" .

pushd /tmp/debpackage
tar xzvf ${NAME}_${VERSION}.orig.tar.gz

cd ${NAME}-${VERSION}

cp -r ${working_dir}/packaging/debian ./
echo "Building on Debian ${DEB}, modifying latest changelog entry."
sed -r -i"" "1s/^${NAME} \((.*)\) (.+;.*)/${NAME} (\1+deb${DEB}) \2/" \
  debian/changelog

echo "Starting build"
DEB_BUILD_OPTIONS=noddebs debuild -us -uc

popd
