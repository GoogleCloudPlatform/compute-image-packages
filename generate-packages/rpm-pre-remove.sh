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

# Daemon
if grep systemd /proc/1/comm; then
  /bin/systemctl stop google-accounts-manager 2> /dev/null
  /bin/systemctl stop google-address-manager 2> /dev/null
  /bin/systemctl stop google-clock-sync-manager 2> /dev/null
else
  /sbin/stop google-address-manager 2> /dev/null
  /sbin/stop google-accounts-manager-service 2> /dev/null
  /sbin/stop google-clock-sync-manager 2> /dev/null
fi

# Start-Up Scripts
if [ ! -x /sbin/initctl ] ; then
  # The following is an eval of the (percent)systemd_preun
  if [ "$1" -eq 0 ] ; then
        # Package removal, not upgrade
        /usr/bin/systemctl --no-reload disable google.service > /dev/null 2>&1 || :
        /usr/bin/systemctl stop google.service > /dev/null 2>&1 || :
        /usr/bin/systemctl --no-reload disable google-startup-scripts.service > /dev/null 2>&1 || :
        /usr/bin/systemctl stop google-startup-scripts.service > /dev/null 2>&1 || :
  fi
fi
