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
Name: gce-disk-expand
Summary: Google Compute Engine root disk expansion module
Version: 2.0.0
Release: %(date +%s).el6
License: GPLv3, Apache Software License
Group: System Environment/Base
URL: https://github.com/GoogleCloudPlatform/compute-image-packages
Requires: gawk, e2fsprogs, file, dracut, grep, util-linux, gdisk
Conflicts: cloud-utils-growpart, cloud-utils, dracut-modules-growroot

# Allow other files in the source that don't end up in the package.
%define _unpackaged_files_terminate_build 0

%description
gce-disk-expand: Automatically resize the root partition on first boot.

This package is adopted from cloud-utils, cloud-initramfs-tools, and
cloud-utils-growpart.

%install
rm -rf $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT
cp -R $RPM_SOURCE_DIR/etc $RPM_BUILD_ROOT
cp -R $RPM_SOURCE_DIR/usr $RPM_BUILD_ROOT

%files
%attr(755,root,root) /etc/init.d/expand-root
%attr(755,root,root) /usr/bin/growpart
%attr(755,root,root) /usr/share/dracut/modules.d/50growroot/growroot-dummy.sh
%attr(755,root,root) /usr/share/dracut/modules.d/50growroot/growroot.sh
%attr(755,root,root) /usr/share/dracut/modules.d/50growroot/install

%post
dracut --force
chkconfig --level 2345 expand-root on

%preun
chkconfig expand-root off

%postun
%dracut --force
