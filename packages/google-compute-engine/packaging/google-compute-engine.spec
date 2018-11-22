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
Version: 2.8.8
Summary: Google Compute Engine guest environment.
License: ASL 2.0
Url: https://github.com/GoogleCloudPlatform/compute-image-packages
Source0: %{name}_%{version}.orig.tar.gz
Requires: curl
Requires: google-compute-engine-oslogin
Requires: python-google-compute-engine = %{version}
Requires: rsyslog

BuildArch: noarch
BuildRequires: systemd

%description
This package contains scripts, configuration, and init files for features
specific to the Google Compute Engine cloud environment.

%description el6
This package contains scripts, configuration, and init files for features
specific to the Google Compute Engine cloud environment.

%description el7
This package contains scripts, configuration, and init files for features
specific to the Google Compute Engine cloud environment.

%package el6
Release 1.el6

Requires: curl
Requires: google-compute-engine-oslogin
Requires: python-google-compute-engine = %{version}
Requires: rsyslog
# Old packages
Obsoletes: google-compute-engine-init
Obsoletes: google-config
Obsoletes: google-startup-scripts
# non-distro version of this package
Obsoletes: google-compute-engine

%package el7
Release 1.el7

Requires: systemd
Requires: curl
Requires: google-compute-engine-oslogin
Requires: python-google-compute-engine = %{version}
Requires: rsyslog
# Old packages
Obsoletes: google-compute-engine-init
Obsoletes: google-config
Obsoletes: google-startup-scripts
# non-distro version of this package
Obsoletes: google-compute-engine

%install
rsync -Pravz src/ %{buildroot}
install -d %{buildroot}%{_unitdir}
rsync -Pravz systemd/*.conf %{buildroot}%{_unitdir}
install -D systemd/*.preset %{buildroot}%{_presetdir}/90-google-compute-engine.preset

%files el6
%defattr(0644,root,root,0755)
/etc/init/*.conf
/etc/udev/rules.d/*.rules
%attr(0755,root,root) %{_bindir}/*
%attr(0755,-,-) /sbin/google-dhclient-script
%attr(0755,-,-) /etc/dhcp/dhclient-exit-hooks/google_set_hostname
%config /etc/modprobe.d/gce-blacklist.conf
%config /etc/rsyslog.d/90-google.conf
%config /etc/sysctl.d/11-gce-network-security.conf

%files el7
%defattr(0644,root,root,0755)
/etc/udev/rules.d/*.rules
%attr(0755,-,-) %{_bindir}/*
%attr(0755,-,-) /etc/dhcp/dhclient.d/google_hostname.sh
%{_unitdir}/*.service
%{_presetdir}/90-google-compute-engine.preset
%config /etc/modprobe.d/gce-blacklist.conf
%config /etc/rsyslog.d/90-google.conf
%config /etc/sysctl.d/11-gce-network-security.conf

%post el6
if [ $1 -eq 2 ]; then
  # New service might not be enabled during upgrade.
  # TODO: this is specifically forbidden-what if the user disabled it?
  systemctl enable google-network-daemon.service
fi

# On upgrade run instance setup again to handle any new configs and restart daemons.
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

%post el7
# On upgrade run instance setup again to handle any new configs and restart daemons.
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

%preun el6
# On uninstall only.
if [ $1 -eq 0 ]; then
  stop -q -n google-accounts-daemon
  stop -q -n google-clock-skew-daemon
  stop -q -n google-network-daemon
  if initctl status google-ip-forwarding-daemon | grep -q 'running'; then
    stop -q -n google-ip-forwarding-daemon
  fi
fi

%preun el7
# On uninstall only.
if [ $1 -eq 0 ]; then
  %systemd_preun google-accounts-daemon.service
  %systemd_preun google-clock-skew-daemon.service
  %systemd_preun google-instance-setup.service
  %systemd_preun google-network-daemon.service
  %systemd_preun google-shutdown-scripts.service
  %systemd_preun google-startup-scripts.service
fi
