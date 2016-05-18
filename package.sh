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

# Build the Linux guest environment deb and rpm packages.

TIMESTAMP="$(date -u +%Y%m%d%H%M%S)"

for CONFIG in 'systemd' 'sysvinit' 'upstart';
do
  fpm \
    -s python \
    -t deb \
    --no-python-fix-name \
    --python-install-bin '/usr/bin' \
    --python-install-lib '/usr/lib/python2.7/site-packages' \
    --after-install "package/$CONFIG/postinst.sh" \
    --before-remove "package/$CONFIG/prerm.sh" \
    --iteration "$TIMESTAMP" \
    setup.py

  fpm \
    -s python \
    -t rpm \
    --no-python-fix-name \
    --python-install-bin '/usr/bin' \
    --python-install-lib '/usr/lib/python2.7/site-packages' \
    --after-install "package/$CONFIG/postinst.sh" \
    --before-remove "package/$CONFIG/prerm.sh" \
    --iteration "$TIMESTAMP" \
    setup.py
done
