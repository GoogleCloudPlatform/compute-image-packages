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
%if 0%{?rhel} == 8
Requires: python3-google-compute-engine = 1:%{version}
%else
Requires: python-google-compute-engine = 1:%{version}
%endif
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
# On upgrade run instance setup again to handle any new configs and restart
# daemons.
if [ $1 -eq 2 ]; then
  /usr/bin/google_instance_setup
  systemctl reload-or-restart google-accounts-daemon.service
  systemctl reload-or-restart google-clock-skew-daemon.service
  systemctl reload-or-restart google-network-daemon.service
fi

%systemd_post google-accounts-daemon.service
%systemd_post google-clock-skew-daemon.service
%systemd_post google-instance-setup.service
%systemd_post google-network-daemon.service
%systemd_post google-shutdown-scripts.service
%systemd_post google-startup-scripts.service

# Remove old services.
if [ -f /lib/systemd/system/google-ip-forwarding-daemon.service ]; then
  systemctl stop --no-block google-ip-forwarding-daemon
  systemctl disable google-ip-forwarding-daemon.service
fi

if [ -f /lib/systemd/system/google-network-setup.service ]; then
  systemctl stop --no-block google-network-setup
  systemctl disable google-network-setup.service
fi

%preun
# On uninstall only.
if [ $1 -eq 0 ]; then
  %systemd_preun google-accounts-daemon.service
  %systemd_preun google-clock-skew-daemon.service
  %systemd_preun google-instance-setup.service
  %systemd_preun google-network-daemon.service
  %systemd_preun google-shutdown-scripts.service
  %systemd_preun google-startup-scripts.service
fi
