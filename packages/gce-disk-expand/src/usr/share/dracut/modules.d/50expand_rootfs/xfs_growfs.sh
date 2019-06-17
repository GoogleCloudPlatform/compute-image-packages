#!/bin/sh
# Copyright 2018 Google Inc. All Rights Reserved.
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

kmsg() {
  echo "xfs_growfs: $@" >/dev/kmsg
}

main() {
  if [ ! -e /tmp/xfs_resize ]; then
    return
  fi

  if ! type xfs_growfs >/dev/null; then
    kmsg "XFS resize requested, but xfs_growfs not installed."
    return
  fi

  kmsg "Mounting filesystem rw for resize."
  if ! $(mount -o rw,remount /sysroot); then
    kmsg "Remount failed."
    return
  fi

  kmsg "Resizing XFS filesystem"
  if ! out=$(xfs_growfs -d /sysroot); then
    kmsg "Failed to resize: ${out}"
  fi
  mount -o ro,remount /sysroot
}

main
