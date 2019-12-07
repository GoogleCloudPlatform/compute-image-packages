# Copyright 2018 Google Inc. All Rights Reserved.
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

# For EL7, if building on CentOS, override dist to be el7.
%if 0%{?rhel} == 7
  %define dist .el7
%endif

Name: google-compute-engine
Epoch: 1
Version: %{_version}
Release: g1%{?dist}
Summary: Google Compute Engine guest environment.
License: ASL 2.0
Url: https://github.com/GoogleCloudPlatform/compute-image-packages
Source0: %{name}_%{version}.orig.tar.gz
Requires: curl
Requires: google-compute-engine-oslogin
Requires: google-guest-agent
Requires: rsyslog

BuildArch: noarch
BuildRequires: systemd

# Allow other files in the source that don't end up in the package.
%define _unpackaged_files_terminate_build 0

%description
This package contains scripts, configuration, and init files for features
specific to the Google Compute Engine cloud environment.

%prep
%autosetup

%install
cp -a src/{etc,usr} %{buildroot}
install -d %{buildroot}/%{_udevrulesdir}
cp -a src/lib/udev/rules.d/* %{buildroot}/%{_udevrulesdir}

%files
%defattr(0644,root,root,0755)
%attr(0755,-,-) %{_bindir}/*
%attr(0755,-,-) /etc/dhcp/dhclient.d/google_hostname.sh
%{_udevrulesdir}/*
%config /etc/modprobe.d/*
%config /etc/rsyslog.d/*
%config /etc/sysctl.d/*

%post
# Remove old services.
for svc in google-ip-forwarding-daemon google-network-setup \
  google-network-daemon google-accounts-daemon google-clock-skew-daemon; do
    if systemctl is-enabled ${svc}.service >/dev/null 2>&1; then
      systemctl disable ${svc}.service
      if [ -d /run/systemd/system ]; then
        systemctl stop ${svc}.service
      fi
    fi
done
