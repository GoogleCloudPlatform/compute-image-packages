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

TIMESTAMP="$(date +%s)"

function build_distro() {
  declare -r distro="$1"
  declare -r pkg_type="$2"
  declare -r py_path="$3"
  declare depends='google-compute-engine-init'
  declare name='google-compute-engine'

  export CONFIG="${init_config}"

  if [[ "${pkg_type}" == 'deb' ]]; then
    depends="${depends}-${distro}"
    name="${name}-${distro}"
  fi

  fpm \
    -s python \
    -t "${pkg_type}" \
    --depends "${depends}" \
    --depends 'python-boto' \
    --depends 'python-setuptools' \
    --iteration "0.${TIMESTAMP}" \
    --maintainer 'gc-team@google.com' \
    --name "${name}" \
    --no-python-fix-name \
    --python-install-bin '/usr/bin' \
    --python-install-lib "${py_path}" \
    --python-install-data "/usr/share/doc/${name}" \
    --rpm-dist "${distro}" \
    setup.py
}

# RHEL/CentOS
build_distro 'el6' 'rpm' '/usr/lib/python2.6/site-packages'
build_distro 'el7' 'rpm' '/usr/lib/python2.7/site-packages'

# Debian
build_distro 'wheezy' 'deb' '/usr/lib/python2.7/dist-packages'
build_distro 'jessie' 'deb' '/usr/lib/python2.7/dist-packages'
