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
# for creating production RPM packages.
#####################################################################

# Run from the top of the source directory.
NAME="google-compute-engine-oslogin"
VERSION="1.3.0"

working_dir=${PWD}
rpm_working_dir=/tmp/rpmpackage/${NAME}-${VERSION}

# Build dependencies.
sudo yum -y install make gcc-c++ libcurl-devel json-c json-c-devel pam-devel policycoreutils-python

# .rpm creation tools.
sudo yum -y install rpmdevtools

rm -rf /tmp/rpmpackage
mkdir -p ${rpm_working_dir}
cp -r ${working_dir}/packaging/rpmbuild ${rpm_working_dir}/
mkdir -p ${rpm_working_dir}/rpmbuild/SOURCES

tar czvf ${rpm_working_dir}/rpmbuild/SOURCES/${NAME}_${VERSION}.orig.tar.gz  --exclude .git --exclude packaging --transform "s/^\./${NAME}-${VERSION}/" .

pushd /tmp/rpmpackage

rpmbuild --define "_topdir ${rpm_working_dir}/rpmbuild" -ba ${rpm_working_dir}/rpmbuild/SPECS/${NAME}.spec
