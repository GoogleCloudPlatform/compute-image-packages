#!/bin/bash
# Copyright 2016 Google Inc. All Rights Reserved.
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

if [ "$1" = purge ]; then
  systemctl stop --no-block google_accounts_daemon
  systemctl stop --no-block google_clock_skew_daemon
  systemctl stop --no-block google_ip_forwarding_daemon

  systemctl --no-reload disable google_instance_setup.service
  systemctl --no-reload disable google_startup_scripts.service
  systemctl --no-reload disable google_shutdown_scripts.service
  systemctl --no-reload disable google_accounts_daemon.service
  systemctl --no-reload disable google_clock_skew_daemon.service
  systemctl --no-reload disable google_ip_forwarding_daemon.service
fi
