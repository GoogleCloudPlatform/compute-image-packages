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

# Stop existing daemons.
systemctl stop --no-block google-accounts-daemon
systemctl stop --no-block google-clock-skew-daemon
systemctl stop --no-block google-network-daemon

# Enable systemd services.
systemctl enable google-accounts-daemon.service
systemctl enable google-clock-skew-daemon.service
systemctl enable google-instance-setup.service
systemctl enable google-network-daemon.service
systemctl enable google-shutdown-scripts.service
systemctl enable google-startup-scripts.service

# Run instance setup manually to prevent startup script execution.
/usr/bin/google_instance_setup

# Start daemons.
systemctl start --no-block google-network-daemon
systemctl start --no-block google-accounts-daemon
systemctl start --no-block google-clock-skew-daemon
