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
if [ -d "/usr/share/google/google_daemon" ]; then
  rm /usr/share/google/google_daemon/*.pyc
fi

#Start-Up scripts
if [ -x /sbin/initctl ] ; then
  # final removal, not an upgrade
  # Remove the line we put in the file before
  if [ "$1" -eq 0 ] ; then
    if [ -f /etc/rc.local ] ; then
      sed -i --follow-symlinks -e '/google-rc-local-has-run/d' /etc/rc.local
    fi
  fi
else
  # This is simply an eval of the (percent)systemd_postun
  /usr/bin/systemctl daemon-reload >/dev/null 2>&1 || :
fi

# Google Compute Engine Image Bundle
if [ -d "/usr/lib/python2.7/site-packages/gcimagebundlelib" ]; then
  rm -f /usr/lib/python2.7/site-packages/gcimagebundlelib/*.pyc
  rmdir --ignore-fail-on-non-empty --parents /usr/lib/python2.7/site-packages/gcimagebundlelib
fi
if [ -d "/usr/lib/python2.6/site-packages/gcimagebundlelib" ]; then
  rm -f /usr/lib/python2.6/site-packages/gcimagebundlelib/*.pyc
  rmdir --ignore-fail-on-non-empty --parents /usr/lib/python2.6/site-packages/gcimagebundlelib
fi
