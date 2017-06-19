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

Name:           google-compute-engine-oslogin
Version:        2.0
Release:        1%{?dist}
Summary:        OS Login Functionality for Google Compute Engine

License:        ASL 2.0
Source0:        %{name}_%{version}.orig.tar.gz

BuildRequires:  gcc-c++
BuildRequires:  make
BuildRequires:  libcurl
BuildRequires:  json-c
BuildRequires:  pam-devel

%define pam_install_path /lib64/security

%description
This package contains several libraries and changes to enable OS Login functionality
for Google Compute Engine.

%prep
%setup

%build
make %{?_smp_mflags} LIBS="-lcurl -ljson-c"

%install
rm -rf %{buildroot}
#%make_install
make install DESTDIR=%{buildroot} NSS_INSTALL_PATH=/%{_lib} PAM_INSTALL_PATH=/lib64/security

%files
%doc
/%{_lib}/libnss_%{name}.so.%{version}
%{pam_install_path}/pam_oslogin_admin.so
%{pam_install_path}/pam_oslogin_login.so
/usr/bin/google_authorized_keys
/usr/bin/google_oslogin_control

%post
/sbin/ldconfig
/usr/bin/google_oslogin_control activate

%preun
/usr/bin/google_oslogin_control deactivate

%postun
/sbin/ldconfig

%changelog
