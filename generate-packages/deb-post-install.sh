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

if [ -x /bin/systemctl ]; then
  # Daemon
  systemctl enable google-accounts-manager.service
  systemctl enable google-address-manager.service
  systemctl enable google-clock-sync-manager.service

  # Start-up scripts
  systemctl enable google.service
  systemctl enable google-startup-scripts.service

  # Daemon
  systemctl start --no-block google-accounts-manager
  systemctl start --no-block google-address-manager
  systemctl start --no-block google-clock-sync-manager

  # Start-up scripts
  systemctl start --no-block google
  systemctl start --no-block google-startup-scripts
else
  # Daemon
  update-rc.d google-address-manager defaults
  update-rc.d google-accounts-manager defaults
  update-rc.d google-clock-sync-manager defaults

  # Start-up scripts
  update-rc.d google defaults
  update-rc.d google-startup-scripts defaults
fi

# add the command to emit the 'google-rc-local-has-run' signal, which will trigger
# startup scripts that should run late at boot.
if ! grep -q 'google-rc-local-has-run' /etc/rc.local; then
    sed -i '/^exit /i \[ -x /sbin/initctl \] && initctl emit --no-wait google-rc-local-has-run || true' /etc/rc.local
fi

# restart the service.
service google-accounts-manager restart && service google-address-manager restart && service google-clock-sync-manager restart

# install gcimagebundle with.
cd /compute-image-packages/gcimagebundle && sudo python setup.py install

# remove temp files
if [ -d "/compute-image-packages/gcimagebundle/build" ]; then
  rm -rf /compute-image-packages/gcimagebundle/build
fi

if [ -d "/compute-image-packages/gcimagebundle/dist" ]; then
  rm -rf /compute-image-packages/gcimagebundle/dist
fi

if [ -d "/compute-image-packages/gcimagebundle" ]; then
  rm -f /compute-image-packages/gcimagebundle/*.pyc /compute-image-packages/gcimagebundle/*.egg  /compute-image-packages/gcimagebundle/*.tar.gz
  rm -rf /compute-image-packages/gcimagebundle/*.egg-info
fi
