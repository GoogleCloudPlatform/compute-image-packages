#!/bin/bash
# Copyright 2019 Google Inc. All Rights Reserved.
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


# Performs two sanity checks for SELinux policy packages:
#
# 1. Validates that the module is version 10, the lowest supported version.
#    Compiling higher versions will result in packages which can't be installed
#    on older systems.
#
# 2. Validates that the binary module matches the rules specified in type
#    enforcement/file context files. To do this, we compile those contents to a
#    temporary package, then decompile both to the intermediate language (CIL)
#    for comparison.

set -e

cd "$(dirname "$0")"

if ! file oslogin.pp | grep -q "mod version 10"; then
  echo "Module is not version 10, it must be compiled on RHEL/CentOS 6 for backwards compatibility."
  echo "\`file oslogin.pp\` returns: $(file oslogin.pp)"
  exit 1
fi

make SELINUX_MODULE=check.pp
/usr/libexec/selinux/hll/pp check.pp >check.cil
/usr/libexec/selinux/hll/pp oslogin.pp >oslogin.cil
if ! out=$(diff check.cil oslogin.cil); then
  echo "Binary policy package oslogin.pp does not match the rules from type enforcement / file context files."
  echo "CIL format diff: ${out}"
  exit 1
fi
