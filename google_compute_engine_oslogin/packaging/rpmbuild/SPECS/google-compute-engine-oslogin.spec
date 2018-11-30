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

Name:           google-compute-engine-oslogin
Version:        1.4.0
Release:        1%{?dist}
Summary:        OS Login Functionality for Google Compute Engine

License:        ASL 2.0
Source0:        %{name}_%{version}.orig.tar.gz

BuildRequires:  boost-devel
BuildRequires:  gcc-c++
BuildRequires:  make
BuildRequires:  libcurl
BuildRequires:  json-c
BuildRequires:  pam-devel
BuildRequires:  policycoreutils-python
Requires:  boost-regex
Requires:  policycoreutils-python

%define pam_install_path /%{_lib}/security

%description
This package contains several libraries and changes to enable OS Login functionality
for Google Compute Engine.

%prep
%setup

%build
make %{?_smp_mflags} LIBS="-lcurl -ljson-c -lboost_regex"

%install
rm -rf %{buildroot}
make install DESTDIR=%{buildroot} NSS_INSTALL_PATH=/%{_lib} PAM_INSTALL_PATH=%{pam_install_path} INSTALL_SELINUX=true

%files
%doc
/%{_lib}/libnss_%{name}-%{version}.so
/%{_lib}/libnss_cache_%{name}-%{version}.so
%{pam_install_path}/pam_oslogin_admin.so
%{pam_install_path}/pam_oslogin_login.so
/usr/bin/google_authorized_keys
/usr/bin/google_oslogin_control
/usr/bin/google_oslogin_nss_cache
/usr/share/selinux/packages/oslogin.pp

%post
/sbin/ldconfig
if [ $1 -gt 1 ]; then  # This is an upgrade.
  if semodule -l | grep -qi oslogin.el6; then
    echo "Removing old SELinux module for OS Login."
    semodule -r oslogin.el6
  fi
fi
echo "Installing SELinux module for OS Login."
semodule -i /usr/share/selinux/packages/oslogin.pp
if [ -e /var/google-sudoers.d ]; then
  fixfiles restore /var/google-sudoers.d
fi

%postun
/sbin/ldconfig
if [ $1 = 0 ]; then  # This is an uninstall.
  if semodule -l|grep -qi oslogin; then
    echo "Removing SELinux module for OS Login."
    semodule -r oslogin
  fi
fi

%changelog
