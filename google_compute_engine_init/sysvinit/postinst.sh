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

update-rc.d google-accounts-daemon defaults
update-rc.d google-clock-skew-daemon defaults
update-rc.d google-instance-setup defaults
update-rc.d google-ip-forwarding-daemon defaults
update-rc.d google-network-setup defaults
update-rc.d google-shutdown-scripts defaults
update-rc.d google-startup-scripts defaults

# Run instance setup.
/etc/init.d/google-instance-setup start

# Enable network interfaces.
/etc/init.d/google-network-setup start
