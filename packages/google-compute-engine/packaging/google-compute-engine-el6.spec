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

Name: google-compute-engine
Version: %{_version}
Release: 1.el6
Summary: Google Compute Engine guest environment.
License: ASL 2.0
Url: https://github.com/GoogleCloudPlatform/compute-image-packages
Source0: %{name}_%{version}.orig.tar.gz
Requires: curl
Requires: google-compute-engine-oslogin
Requires: python-google-compute-engine = %{version}
Requires: rsyslog
# Old packages.
Obsoletes: google-compute-engine-init
Obsoletes: google-config
Obsoletes: google-startup-scripts

BuildArch: noarch

# Allow other files in the source that don't end up in the package.
%define _unpackaged_files_terminate_build 0

%description
This package contains scripts, configuration, and init files for features
specific to the Google Compute Engine cloud environment.

%prep
%autosetup

%install
cp -a src/{etc,usr} %{buildroot}
install -d %{buildroot}/lib/
cp -a src/lib/udev %{buildroot}/lib

%files
%defattr(0644,root,root,0755)
%attr(0755,-,-) %{_bindir}/*
%attr(0755,-,-) %{_sbindir}/*
/lib/udev/rules.d/*
/etc/init/*.conf
/etc/dhcp/dhclient-exit-hooks
%config /etc/modprobe.d/*
%config /etc/rsyslog.d/*
%config /etc/sysctl.d/*

%post
if [ $1 -eq 2 ]; then
  # New service might not be enabled during upgrade.
  systemctl enable google-network-daemon.service
fi

# On upgrade run instance setup again to handle any new configs and restart
# daemons.
if [ $1 -eq 2 ]; then
  stop -q -n google-accounts-daemon
  stop -q -n google-clock-skew-daemon
  stop -q -n google-network-daemon
  /usr/bin/google_instance_setup
  start -q -n google-accounts-daemon
  start -q -n google-clock-skew-daemon
  start -q -n google-network-daemon
fi

if initctl status google-ip-forwarding-daemon | grep -q 'running'; then
  stop -q -n google-ip-forwarding-daemon
fi

%preun
# On uninstall only.
if [ $1 -eq 0 ]; then
  stop -q -n google-accounts-daemon
  stop -q -n google-clock-skew-daemon
  stop -q -n google-network-daemon
  if initctl status google-ip-forwarding-daemon | grep -q 'running'; then
    stop -q -n google-ip-forwarding-daemon
  fi
fi
