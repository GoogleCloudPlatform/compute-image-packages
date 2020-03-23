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
Epoch: 1
Version: %{_version}
Release: g1
License: Apache Software License
Group: System Environment/Base
URL: https://github.com/GoogleCloudPlatform/compute-image-packages
Source0: %{name}_%{version}.orig.tar.gz
Requires: e2fsprogs, dracut, grep, util-linux, parted, gdisk
Conflicts: dracut-modules-growroot

BuildRequires: rsync

# Allow other files in the source that don't end up in the package.
%define _unpackaged_files_terminate_build 0

%description
This package resizes the root partition on first boot using parted.

%prep
%autosetup

%install
mv src/expandfs-lib.sh src/usr/share/dracut/modules.d/50expand_rootfs/
%if 0%{?rhel} >= 7
  ./dracut6_7.sh
%endif
rsync -Pravz src/ %{buildroot}

%files
%if 0%{?rhel} >= 7
 %attr(755,root,root) /usr/lib/dracut/modules.d/50expand_rootfs/*
%else
 %attr(755,root,root) /usr/share/dracut/modules.d/50expand_rootfs/*
%endif

%post
dracut --force

%postun
dracut --force
