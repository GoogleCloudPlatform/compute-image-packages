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

if [ "$1" = purge ]; then
  if [ -x /bin/systemctl ]; then
    # Daemon
    systemctl stop --no-block google-address-manager
    systemctl stop --no-block google-accounts-manager
    systemctl stop --no-block google-clock-sync-manager

    # Start-Up scripts
    systemctl --no-reload disable google.service
    systemctl --no-reload disable google-startup-scripts.service

    # Daemon
    systemctl --no-reload disable google-address-manager
    systemctl --no-reload disable google-accounts-manager
    systemctl --no-reload disable google-clock-sync-manager

    # Start-Up scripts
    systemctl stop --no-block google
    systemctl stop --no-block google-startup-scripts
  else
    # Daemon
    update-rc.d google-address-manager remove
    update-rc.d google-accounts-manager remove
    update-rc.d google-clock-sync-manager remove

    # Start-Up scripts
    update-rc.d google remove
    update-rc.d google-startup-scripts remove
  fi

  # We add this line in the postinst, so we should remove it here on purge.
  sed -i -e '/google-rc-local-has-run/d' /etc/rc.local
fi

if [ -d "/usr/share/google/google_daemon" ]; then
  rm -f /usr/share/google/google_daemon/*.pyc
fi
