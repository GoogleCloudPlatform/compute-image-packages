#!/bin/bash
# Copyright 2016 Google Inc. All Rights Reserved.
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

if [[ -d $1 ]]; then
  echo "Saving packages to $1"
  RPM_DEST=$1
else
  RPM_DEST="/tmp"
fi

RPM_TOP=$(mktemp -d)
SPEC_FILE="gce-disk-expand-el6.spec"

echo "Setup"
mkdir -p ${RPM_TOP}/SOURCES/etc/init.d
mkdir -p ${RPM_TOP}/SOURCES/usr/bin
mkdir -p ${RPM_TOP}/SOURCES/usr/share/dracut/modules.d/50growroot

cp expand-root ${RPM_TOP}/SOURCES/etc/init.d
cp third_party/cloud-utils/* ${RPM_TOP}/SOURCES/usr/bin
cp third_party/dracut-modules-growroot/* \
  ${RPM_TOP}/SOURCES/usr/share/dracut/modules.d/50growroot

echo "Building"
rpmbuild --define "_topdir ${RPM_TOP}" -ba ${SPEC_FILE}

echo "Copying rpm's to ${RPM_DEST}"
cp ${RPM_TOP}/RPMS/x86_64/*.rpm ${RPM_DEST}
cp ${RPM_TOP}/SRPMS/*.rpm ${RPM_DEST}
ls -l ${RPM_DEST}/*.rpm

echo "Cleaning up"
rm -Rf ${RPM_TOP}
