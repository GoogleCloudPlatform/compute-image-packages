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

COMMON_FILES=(
  'rsyslog/90-google.conf=/etc/rsyslog.d/90-google.conf'
  'sysctl/11-gce-network-security.conf=/etc/sysctl.d/11-gce-network-security.conf'
  'udev/64-gce-disk-removal.rules=/etc/udev/rules.d/64-gce-disk-removal.rules'
  'udev/65-gce-disk-naming.rules=/etc/udev/rules.d/65-gce-disk-naming.rules')
TIMESTAMP="$(date +%s)"

function build_distro() {
  declare -r distro="$1"
  declare -r pkg_type="$2"
  declare -r init_config="$3"
  declare -r init_prefix="$4"
  declare depends='google-compute-engine'
  declare files=("$@")
  declare file_pattern='*[^.sh]'
  declare init_files=(${init_config}/${file_pattern})
  declare name='google-config'

  for ((i=0; i<${#init_files[@]}; i++)); do
    file_name="$(basename ${init_files[$i]})"
    file_entry="${init_config}/${file_name}=${init_prefix}/${file_name}"
    init_files[$i]="$file_entry"
  done

  if [[ "${pkg_type}" == 'deb' ]]; then
    depends="google-compute-engine-${distro}"
    name="${name}-${distro}"
  fi

  fpm \
    -s dir \
    -t "${pkg_type}" \
    --after-install "${init_config}/postinst.sh" \
    --before-remove "${init_config}/prerm.sh" \
    --depends "${depends}" \
    --description 'Google Compute Engine Linux guest configuration' \
    --iteration "0.${TIMESTAMP}" \
    --license 'Apache Software License' \
    --maintainer 'gc-team@google.com' \
    --name "${name}" \
    --replaces 'gce-startup-scripts' \
    --replaces 'google-startup-scripts' \
    --rpm-dist "${distro}" \
    --url 'https://github.com/GoogleCloudPlatform/compute-image-packages' \
    --vendor 'Google Compute Engine Team' \
    --version '2.0.0' \
    "${COMMON_FILES[@]}" \
    "${init_files[@]}" \
    "${files[@]:4}"
}

# RHEL/CentOS
build_distro 'el6' 'rpm' 'upstart' '/etc/init' \
  'bin/set_hostname=/etc/dhcp/dhclient-exit-hooks'

build_distro 'el7' 'rpm' 'systemd' '/usr/lib/systemd/system' \
  'bin/set_hostname=/usr/bin/set_hostname' \
  'dhcp/google_hostname.sh=/etc/dhcp/dhclient.d/google_hostname.sh'

# Debian
build_distro 'wheezy' 'deb' 'sysvinit' '/etc/init.d' \
  'bin/set_hostname=/etc/dhcp/dhclient-exit-hooks.d/set_hostname'

build_distro 'jessie' 'deb' 'systemd' '/usr/lib/systemd/system' \
  'bin/set_hostname=/etc/dhcp/dhclient-exit-hooks.d/set_hostname'
