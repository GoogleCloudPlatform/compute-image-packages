# Copyright 2019 Google Inc. All Rights Reserved.
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

Name: python3-google-compute-engine
Epoch: 1
Version: %{_version}
Release: g1%{?dist}
Summary: Google Compute Engine python3 library
License: ASL 2.0
Url: https://github.com/GoogleCloudPlatform/compute-image-packages
Source0: %{name}_%{version}.orig.tar.gz

BuildArch: noarch
BuildRequires: python36-devel python3-setuptools

Requires: python3-setuptools

%description
Google Compute Engine python library for Python 3.x.

%prep
%autosetup

%build
%py3_build

%install
%py3_install

%files
%{python3_sitelib}/google_compute_engine/
%{python3_sitelib}/google_compute_engine*.egg-info/
%{_bindir}/google_accounts_daemon
%{_bindir}/google_clock_skew_daemon
%{_bindir}/google_instance_setup
%{_bindir}/google_metadata_script_runner
%{_bindir}/google_network_daemon
