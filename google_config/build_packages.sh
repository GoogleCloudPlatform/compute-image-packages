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

#/ Usage: build_packages.sh [options]
#/
#/ Build the package containing non-Python scripts and guest configuration.
#/
#/ OPTIONS:
#/   -h             Show this message
#/   -o DISTRO,...  Build only specified distros

function usage() {
  grep '^#/' < "$0" | cut -c 4-
}

function build_distro() {
  declare -r distro="$1"
  declare -r pkg_type="$2"
  declare files=("$@")
  declare name='google-config'

  if [[ "${pkg_type}" == 'deb' ]]; then
    name="${name}-${distro}"
  fi

  fpm \
    -s dir \
    -t "${pkg_type}" \
    --description 'Google Compute Engine Linux guest configuration' \
    --iteration "0.${TIMESTAMP}" \
    --license 'Apache Software License' \
    --maintainer 'gc-team@google.com' \
    --name "${name}" \
    --rpm-dist "${distro}" \
    --url 'https://github.com/GoogleCloudPlatform/compute-image-packages' \
    --vendor 'Google Compute Engine Team' \
    --version '2.1.1' \
    "${COMMON_FILES[@]}" \
    "${files[@]:2}"
}

COMMON_FILES=(
  'rsyslog/90-google.conf=/etc/rsyslog.d/90-google.conf'
  'sysctl/11-gce-network-security.conf=/etc/sysctl.d/11-gce-network-security.conf'
  'udev/64-gce-disk-removal.rules=/etc/udev/rules.d/64-gce-disk-removal.rules'
  'udev/65-gce-disk-naming.rules=/etc/udev/rules.d/65-gce-disk-naming.rules')
TIMESTAMP="$(date +%s)"

while getopts 'ho:' OPTION; do
  case "$OPTION" in
    h)
      usage
      exit 2
      ;;
    o)
      set -f
      IFS=','
      BUILD=($OPTARG)
      set +f
      ;;
    ?)
      usage
      exit
      ;;
  esac
done

if [ -z "$BUILD" ]; then
  BUILD=('el6' 'el7' 'jessie' 'stretch')
fi

for build in "${BUILD[@]}"; do
  case "$build" in
    el6) # RHEL/CentOS 6
      build_distro 'el6' 'rpm' \
        'bin/set_hostname=/etc/dhcp/dhclient-exit-hooks' \
        'sbin/google-dhclient-script=/sbin/google-dhclient-script'
      ;;
    el7) # RHEL/CentOS 7
      build_distro 'el7' 'rpm' \
        'bin/set_hostname=/usr/bin/set_hostname' \
        'dhcp/google_hostname.sh=/etc/dhcp/dhclient.d/google_hostname.sh'
      ;;
    wheezy) # Debian 7
      build_distro 'wheezy' 'deb' \
        'bin/set_hostname=/etc/dhcp/dhclient-exit-hooks.d/set_hostname'
      ;;
    jessie) # Debian 8
      build_distro 'jessie' 'deb' \
        'bin/set_hostname=/etc/dhcp/dhclient-exit-hooks.d/set_hostname'
      ;;
    stretch) # Debian 9
      build_distro 'stretch' 'deb' \
        'bin/set_hostname=/etc/dhcp/dhclient-exit-hooks.d/set_hostname'
      ;;
    *)
      echo "Invalid build '${build}'. Use 'el6', 'el7', 'wheezy', 'jessie', or 'stretch'."
      ;;
  esac
done
