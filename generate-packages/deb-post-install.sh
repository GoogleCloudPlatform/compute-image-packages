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

# Copy start up scripts.
sudo cp -R /compute-image-packages/{google-daemon/{etc,usr},google-startup-scripts/{etc,usr,lib}} /

# add start up scripts to configruation.
sudo update-rc.d google-startup-scripts defaults && sudo update-rc.d google-accounts-manager defaults && sudo update-rc.d google-address-manager defaults && sudo update-rc.d google-clock-sync-manager defaults

# restart the service.
sudo service google-accounts-manager restart && sudo service google-address-manager restart && sudo service google-clock-sync-manager restart

# install gcimagebundle with.
cd /compute-image-packages/gcimagebundle && sudo python setup.py install