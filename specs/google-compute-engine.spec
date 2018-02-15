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

Name: google-compute-engine
Version: 2.7.7
Release: 1%{?dist}
Summary: Google Compute Engine guest environment.
License: ASL 2.0
Url: https://github.com/GoogleCloudPlatform/compute-image-packages
Source0: %{name}_%{version}.orig.tar.gz

BuildArch: noarch
BuildRequires: python2-devel python-setuptools python-boto
%if 0%{?el7}
BuildRequires: systemd
%endif

Requires: curl
Requires: google-compute-engine-oslogin
Requires: ntp
Requires: python-google-compute-engine = %{version}
Requires: python-setuptools
Requires: rsyslog
%if 0%{?el7}
Requires: systemd
%endif

Obsoletes: google-compute-engine-init
Obsoletes: google-config
Obsoletes: google-startup-scripts
Conflicts: google-compute-engine-init
Conflicts: google-config
Conflicts: google-startup-scripts

%description
This package contains scripts, configuration, and init files for features specific to the Google Compute Engine cloud environment.

%prep
%autosetup -n compute-image-packages

%install
mkdir -p %{buildroot}%{_bindir}
mkdir -p %{buildroot}/etc/dhcp
mkdir -p %{buildroot}/etc/modprobe.d
mkdir -p %{buildroot}/etc/rsyslog.d
mkdir -p %{buildroot}/etc/sysctl.d
mkdir -p %{buildroot}/etc/udev/rules.d

cp google_config/modprobe/gce-blacklist.conf %{buildroot}/etc/modprobe.d/
cp google_config/rsyslog/90-google.conf %{buildroot}/etc/rsyslog.d/
cp google_config/sysctl/11-gce-network-security.conf  %{buildroot}/etc/sysctl.d/
cp google_config/udev/*.rules %{buildroot}/etc/udev/rules.d/

# Install the python package to get the entry scripts.
python setup.py install --prefix=%{_prefix} --root %{buildroot}
rm -Rf %{buildroot}/usr/lib/python*

%if 0%{?el6}
mkdir %{buildroot}/sbin
mkdir -p %{buildroot}/etc/init
cp google_compute_engine_init/upstart/*.conf %{buildroot}/etc/init/
cp google_config/bin/google_set_hostname %{buildroot}/etc/dhcp/dhclient-exit-hooks
cp google_config/sbin/google-dhclient-script %{buildroot}/sbin/
%endif

%if 0%{?el7}
mkdir -p %{buildroot}/etc/dhcp/dhclient.d
mkdir -p %{buildroot}%{_unitdir}
mkdir -p %{buildroot}%{_presetdir}
cp google_compute_engine_init/systemd/*.service %{buildroot}%{_unitdir}
cp google_compute_engine_init/systemd/90-google-compute-engine.preset %{buildroot}%{_presetdir}/90-google-compute-engine.preset
cp google_config/bin/google_set_hostname %{buildroot}%{_bindir}
cp google_config/dhcp/google_hostname.sh %{buildroot}/etc/dhcp/dhclient.d/google_hostname.sh
%endif


%files
%defattr(0644,root,root,0755)
%if 0%{?el6}
%attr(0755,root,root) /sbin/google-dhclient-script
%attr(0755,root,root) /etc/dhcp/dhclient-exit-hooks
/etc/init/*.conf
%endif
%if 0%{?el7}
%attr(0755,root,root) /etc/dhcp/dhclient.d/google_hostname.sh
%{_unitdir}/*.service
%{_presetdir}/90-google-compute-engine.preset
%endif
%config /etc/modprobe.d/gce-blacklist.conf
%config /etc/rsyslog.d/90-google.conf
%config /etc/sysctl.d/11-gce-network-security.conf
/etc/udev/rules.d/*.rules
%attr(0755,root,root) %{_bindir}/*


%post
%if 0%{?el6}
# On upgrade run instance setup again to handle any new configs and restart daemons.
if [ $1 -eq 2 ]; then
  stop -q -n ip-forwarding-daemon
  stop -q -n google-accounts-daemon
  stop -q -n google-clock-skew-daemon
  stop -q -n google-network-daemon
  /usr/bin/google_instance_setup
  start -q -n google-accounts-daemon
  start -q -n google-clock-skew-daemon
  start -q -n google-network-daemon
fi

# Install google-compute-engine from pypi into the SCL environment if it exists.
# The google-compute-engine package in the SCL environment needs to be maintained
# along with the python 2.6 package from the RPM. In particular, SCL python2.7
# packages that use boto will need the up to date package available in case of
# any changes in the shared libraries.
if [ -d /opt/rh/python27/root/usr/lib/python2.7/site-packages/google_compute_engine ]; then
  scl enable python27 "pip2.7 install --upgrade google_compute_engine"
fi
%endif

%if 0%{?el7}
%systemd_post google-accounts-daemon.service
%systemd_post google-clock-skew-daemon.service
%systemd_post google-instance-setup.service
%systemd_post google-network-daemon.service
%systemd_post google-shutdown-scripts.service
%systemd_post google-startup-scripts.service
# On upgrade run instance setup again to handle any new configs and restart daemons.
if [ $1 -eq 2 ]; then
  /usr/bin/google_instance_setup
  systemctl reload-or-restart google-accounts-daemon.service
  systemctl reload-or-restart google-clock-skew-daemon.service
  systemctl reload-or-restart google-network-daemon.service
fi
%endif


%preun
# On uninstall only.
if [ $1 -eq 0 ]; then
%if 0%{?el6}
  stop -q -n google-accounts-daemon
  stop -q -n google-clock-skew-daemon
  stop -q -n google-network-daemon
%endif
%if 0%{?el7}
  %systemd_preun google-accounts-daemon.service
  %systemd_preun google-clock-skew-daemon.service
  %systemd_preun google-instance-setup.service
  %systemd_preun google-network-daemon.service
  %systemd_preun google-shutdown-scripts.service
  %systemd_preun google-startup-scripts.service
%endif
fi
