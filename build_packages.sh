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
  declare -r py_pkt="$4"
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
    --depends "${py_pkt}-boto" \
    --depends "${py_pkt}-setuptools" \
    --iteration "0.${TIMESTAMP}" \
    --maintainer 'gc-team@google.com' \
    --name "${name}" \
    --no-python-fix-name \
    --python-install-bin '/usr/bin' \
    --python-install-lib "${py_path}" \
    --python-install-data "/usr/share/doc/${name}" \
    --rpm-dist "${distro}" \
    --python-scripts-executable "/usr/bin/${py_pkt}" \
    setup.py
}

# RHEL/CentOS
build_distro 'el5' 'rpm' '/usr/lib/python2.6/site-packages' 'python26'
build_distro 'el6' 'rpm' '/usr/lib/python2.6/site-packages' 'python'
build_distro 'el7' 'rpm' '/usr/lib/python2.7/site-packages' 'python'

# Debian
build_distro 'wheezy' 'deb' '/usr/lib/python2.7/dist-packages' 'python'
build_distro 'jessie' 'deb' '/usr/lib/python2.7/dist-packages' 'python'
