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

  /bin/systemctl enable /usr/lib/systemd/system/google-accounts-manager.service
  /bin/systemctl enable /usr/lib/systemd/system/google-address-manager.service
  /bin/systemctl enable \
    /usr/lib/systemd/system/google-clock-sync-manager.service

  /bin/systemctl start google-accounts-manager
  /bin/systemctl start google-address-manager
  /bin/systemctl start google-clock-sync-manager
else
  /sbin/stop google-address-manager 2> /dev/null
  /sbin/stop google-accounts-manager-service 2> /dev/null
  /sbin/stop google-clock-sync-manager 2> /dev/null
  # Kill the old version that can't be stopped via above method
  kill $(ps ax | \
    egrep 'python\s/usr/share/google/google_daemon/manage_addresses.py' | \
    awk '{print $1}') 2> /dev/null
  /sbin/start google-address-manager
  /sbin/start google-accounts-manager-service
  /sbin/start google-clock-sync-manager
fi

# Start-up Scripts
if [ -x /sbin/initctl ] ; then
  if [ "$1" -eq 1 ] ; then
    # first install, not an upgrade
    # Add the needed upstart job emission to /etc/rc.local, conditional on upstart
    # being present, but only if it's not already in the file.

    UPSTART_LINE="[ -x /sbin/initctl ] && /sbin/initctl emit --no-wait google-rc-local-has-run || true"
    SED_COMMANDS="$(cat <<EOF
# Add the upstart line before the first non-comment, non-empty line, then quit.
# The sed 'i' command does insert-before; the sed 'q' command quits processing.
/^[^#]/{ i ${UPSTART_LINE}
q}
# If no such line exists, add to the end of the file.
# The sed 'a' command does append, aka insert-after.
\$ a ${UPSTART_LINE}
EOF
    )"

    # Only change /etc/rc.local if no line exactly matches "${UPSTART_LINE}".
    if ! grep -q -x -F "${UPSTART_LINE}" /etc/rc.local; then
      sed -i --follow-symlinks -e "${SED_COMMANDS}" /etc/rc.local
    fi
  fi
else
  # Here I was forced to copy the results of rpm --eval "(percent)systemd_post"
  # because of a limitation in our RPM build system
  if [ "$1" -eq 1 ] ; then
        # Initial installation
        /usr/bin/systemctl preset google.service >/dev/null 2>&1 || :
        /usr/bin/systemctl preset google-startup-scripts.service >/dev/null 2>&1 || :
  fi
fi

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
