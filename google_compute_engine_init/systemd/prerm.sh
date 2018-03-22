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
  systemctl stop --no-block google-accounts-daemon
  systemctl stop --no-block google-clock-skew-daemon
  systemctl stop --no-block google-network-daemon

  systemctl --no-reload disable google-accounts-daemon.service
  systemctl --no-reload disable google-clock-skew-daemon.service
  systemctl --no-reload disable google-instance-setup.service
  systemctl --no-reload disable google-network-daemon.service
  systemctl --no-reload disable google-shutdown-scripts.service
  systemctl --no-reload disable google-startup-scripts.service
fi
