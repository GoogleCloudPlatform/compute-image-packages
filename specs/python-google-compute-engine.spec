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

# Force the dist to be el7 to avoid el7.centos.
%if 0%{?rhel} == 7
  %define dist .el7
%endif

Name: python-google-compute-engine
Version: 2.8.6
Release: 1%{?dist}
Summary: Google Compute Engine python library
License: ASL 2.0
Url: https://github.com/GoogleCloudPlatform/compute-image-packages
Source0: google-compute-engine_%{version}.orig.tar.gz

BuildArch: noarch
BuildRequires: python2-devel python-setuptools python-boto

Requires: python-boto python-setuptools

Provides: python2-google-compute-engine

Obsoletes: google-compute-daemon
Obsoletes: google-startup-scripts
Conflicts: google-compute-daemon
Conflicts: google-startup-scripts

%description
Google Compute Engine python library for Python 2.x.

%prep
%autosetup -n compute-image-packages

%build
python setup.py build

%install
python setup.py install --prefix=%{_prefix} --root %{buildroot}
rm -Rf %{buildroot}/usr/bin

%files
%{python_sitelib}/*
