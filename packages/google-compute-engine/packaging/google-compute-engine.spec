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
install -d %{buildroot}/{%{_unitdir},%{_presetdir},%{_udevrulesdir}}
cp -a src/lib/systemd/system/* %{buildroot}/%{_unitdir}
cp -a src/lib/systemd/system-preset/* %{buildroot}/%{_presetdir}
cp -a src/lib/udev/rules.d/* %{buildroot}/%{_udevrulesdir}

%files
%defattr(0644,root,root,0755)
%attr(0755,-,-) %{_bindir}/*
%attr(0755,-,-) /etc/dhcp/dhclient.d/google_hostname.sh
%{_udevrulesdir}/*
%{_unitdir}/*
%{_presetdir}/*
%config /etc/modprobe.d/*
%config /etc/rsyslog.d/*
%config /etc/sysctl.d/*

%post
%systemd_post google-shutdown-scripts.service
%systemd_post google-startup-scripts.service

# Remove old services.
for svc in google-ip-forwarding-daemon google-network-setup \
  google-network-daemon google-accounts-daemon google-clock-skew-daemon; do
    if [ -f /lib/systemd/system/${svc}.service ]; then
      systemctl stop ${svc}.service
      systemctl disable ${svc}.service
    fi
done

%preun
# On uninstall only.
if [ $1 -eq 0 ]; then
  %systemd_preun google-shutdown-scripts.service
  %systemd_preun google-startup-scripts.service
fi
