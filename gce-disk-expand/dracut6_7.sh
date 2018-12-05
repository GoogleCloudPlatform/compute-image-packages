#!/bin/bash
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

# Modifies rhel6 dracut for rhel7.

mv src/usr/share src/usr/lib
pushd src/usr/lib/dracut/modules.d/50expand_rootfs

cat >module-setup.sh <<EOF
#!/bin/bash

check() {
`grep -iv ^'#!' check`
}

install() {
`grep -iv ^'#!' install`
}
EOF

rm install check
popd
