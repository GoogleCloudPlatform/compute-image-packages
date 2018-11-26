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

############################## WARNING ##############################
# This script is for testing purposes only. It is not intended
# for creating production Debian packages.
#####################################################################

NAME="google-compute-engine-oslogin"
VERSION="1.3.2"
working_dir=${PWD}

if [[ $(basename "$working_dir") == $NAME ]]; then
  echo "packaging scripts must be run from top of package dir"
  exit 1
fi

# Build dependencies.
sudo apt-get -y install make g++ libcurl4-openssl-dev libjson-c-dev libpam-dev

# .deb creation tools.
sudo apt-get -y install debhelper devscripts build-essential

rm -rf /tmp/debpackage
tar czvf /tmp/debpackage/${NAME}_${VERSION}.orig.tar.gz  --exclude .git --exclude packaging --transform "s/^\./${NAME}-${VERSION}/" .

pushd /tmp/debpackage
tar xzvf ${NAME}_${VERSION}.orig.tar.gz

cd ${NAME}-${VERSION}

cp -r ${working_dir}/packaging/debian ./

debuild -us -uc

popd
