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
#/ Build the package that contains init configuration for the
#/ google-compute-engine Python package.
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
  declare -r init_config="$3"
  declare -r init_prefix="$4"
  declare py_depends='google-compute-engine'
  declare config_depends='google-config'
  declare file_pattern='*[^.sh]'
  declare init_files=(${init_config}/${file_pattern})
  declare name='google-compute-engine-init'

  for ((i=0; i<${#init_files[@]}; i++)); do
    file_name="$(basename ${init_files[$i]})"
    file_entry="${init_config}/${file_name}=${init_prefix}/${file_name}"
    init_files[$i]="$file_entry"
  done

  if [[ "${pkg_type}" == 'deb' ]]; then
    py_depends="${py_depends}-${distro}"
    config_depends="${config_depends}-${distro}"
    name="${name}-${distro}"
  fi

  fpm \
    -s dir \
    -t "${pkg_type}" \
    --after-install "${init_config}/postinst.sh" \
    --before-remove "${init_config}/prerm.sh" \
    --depends "${py_depends}" \
    --depends "${config_depends}" \
    --description 'Google Compute Engine Linux initialization scripts' \
    --iteration "0.${TIMESTAMP}" \
    --license 'Apache Software License' \
    --maintainer 'gc-team@google.com' \
    --name "${name}" \
    --replaces 'gce-daemon' \
    --replaces 'gce-startup-scripts' \
    --replaces 'google-compute-daemon' \
    --replaces 'google-startup-scripts' \
    --rpm-dist "${distro}" \
    --rpm-trigger-after-target-uninstall \
      "google-compute-daemon: ${init_config}/rpm_replace" \
    --url 'https://github.com/GoogleCloudPlatform/compute-image-packages' \
    --vendor 'Google Compute Engine Team' \
    --version '2.1.2' \
    "${init_files[@]}"
}

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
      build_distro 'el6' 'rpm' 'upstart' '/etc/init'
      ;;
    el7) # RHEL/CentOS 7
      build_distro 'el7' 'rpm' 'systemd' '/usr/lib/systemd/system'
      ;;
    wheezy) # Debian 7
      build_distro 'wheezy' 'deb' 'sysvinit' '/etc/init.d'
      ;;
    jessie) # Debian 8
      build_distro 'jessie' 'deb' 'systemd' '/usr/lib/systemd/system'
      ;;
    stretch) # Debian 9
      build_distro 'stretch' 'deb' 'systemd' '/usr/lib/systemd/system'
      ;;
    *)
      echo "Invalid build '${build}'. Use 'el6', 'el7', 'wheezy', 'jessie', or 'stretch'."
      ;;
  esac
done
