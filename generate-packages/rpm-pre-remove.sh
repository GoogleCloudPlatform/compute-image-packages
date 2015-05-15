#!/bin/bash
# Copyright 2015 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# remove start up scripts from configuration.
sudo chkconfig --del google-startup-scripts && sudo chkconfig --del google-accounts-manager && sudo chkconfig --del google-address-manager && sudo chkconfig --del google-clock-sync-manager

# Remove files of Google daemon
sudo rm -f /etc/init/google-accounts-manager-service.conf
sudo rm -f /etc/init/google-accounts-manager-task.conf
sudo rm -f /etc/init/google-address-manager.conf
sudo rm -f /etc/init/google-clock-sync-manager.conf

sudo rm -f /etc/rc.d/google-accounts-manager
sudo rm -f /etc/rc.d/google-address-manager
sudo rm -f /etc/rc.d/google-clock-sync-manager

sudo rm -f /usr/lib/systemd/system/google-accounts-manager.service
sudo rm -f /usr/lib/systemd/system/google-address-manager.service
sudo rm -f /usr/lib/systemd/system/google-clock-sync-manager.service

sudo rm -f /usr/share/google/google_daemon/accounts_manager_daemon.py
sudo rm -f /usr/share/google/google_daemon/accounts_manager.py
sudo rm -f /usr/share/google/google_daemon/accounts.py
sudo rm -f /usr/share/google/google_daemon/address_manager.py
sudo rm -f /usr/share/google/google_daemon/desired_accounts.py
sudo rm -f /usr/share/google/google_daemon/manage_accounts.py
sudo rm -f /usr/share/google/google_daemon/manage_addresses.py
sudo rm -f /usr/share/google/google_daemon/manage_clock_sync.py
sudo rm -f /usr/share/google/google_daemon/metadata_watcher.py
sudo rm -f /usr/share/google/google_daemon/utils.py


# Remove files of Google startup scripts
sudo rm -f /etc/init/google.conf
sudo rm -f /etc/init/google_run_shutdown_scripts.conf
sudo rm -f /etc/init/google_run_startup_scripts.conf

sudo rm -f /etc/rc.d/google
sudo rm -f /etc/rc.d/google-startup-scripts

sudo rm -f /etc/rsyslog.d/90-google.conf
sudo rm -f /etc/sysctl.d/11-gce-network-security.conf

sudo rm -f /usr/lib/udev/rules.d/64-gce-disk-removal.rules
sudo rm -f /usr/lib/udev/rules.d/65-gce-disk-naming.rules

sudo rm -f /usr/lib/systemd/system/google-accounts-manager.service
sudo rm -f /usr/lib/systemd/system/google-startup-scripts.service

sudo rm -f /usr/lib/systemd/system-preset/50-google.preset

sudo rm -f /share/google/boto/boot_setup.py
sudo rm -f /share/google/boto_plugins/compute_auth.py
sudo rm -f /share/google/fetch_script
sudo rm -f /share/google/first-boot
sudo rm -f /share/google/get_metadata_value
sudo rm -f /share/google/onboot
sudo rm -f /share/google/regenerate-host-keys
sudo rm -f /share/google/run-scripts
sudo rm -f /share/google/run-shutdown-scripts
sudo rm -f /share/google/run-startup-scripts
sudo rm -f /share/google/safe_format_and_mount
sudo rm -f /share/google/set-hostname
sudo rm -f /share/google/set-interrupts
sudo rm -f /share/google/virtionet-irq-affinity
