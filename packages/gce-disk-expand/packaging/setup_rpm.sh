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
NAME="gce-disk-expand"
VERSION="2.0.0"

working_dir=${PWD}
rpm_working_dir=/tmp/rpmpackage/

if [[ $(basename "$working_dir") == $NAME ]]; then
  echo "packaging scripts must be run from top of package dir"
  exit 1
fi

# .rpm creation tools.
sudo yum -y install rpmdevtools

rm -rf ${rpm_working_dir}
mkdir -p ${rpm_working_dir}/{SOURCES,SPECS}
cp packaging/${NAME}.spec ${rpm_working_dir}/SPECS/

tar czvf ${rpm_working_dir}/SOURCES/${NAME}_${VERSION}.orig.tar.gz  --exclude .git --exclude packaging --transform "s/^\./${NAME}-${VERSION}/" .

rpmbuild --define "_topdir ${rpm_working_dir}/" -ba ${rpm_working_dir}/SPECS/${NAME}.spec
