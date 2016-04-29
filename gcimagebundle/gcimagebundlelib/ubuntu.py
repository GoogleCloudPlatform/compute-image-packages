# Copyright 2013 Google Inc. All Rights Reserved.
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

"""Ubuntu specific platform info."""

import csv
import os
from gcimagebundlelib import linux


class Ubuntu(linux.LinuxPlatform):
  """Ubuntu specific information."""

  @staticmethod
  def IsThisPlatform(root='/'):
    release_file = root + '/etc/lsb-release'
    if os.path.exists(release_file):
      (_, _, flavor, _) = Ubuntu.ParseLsbRelease(release_file)
      if flavor and flavor.lower() == 'ubuntu':
        return True
    return False

  @staticmethod
  def ParseLsbRelease(release_file='/etc/lsb-release'):
    """Parses the /etc/lsb-releases file."""
    release_info = {}
    for line in csv.reader(open(release_file), delimiter='='):
      if len(line) > 1:
        release_info[line[0]] = line[1]
    if ('DISTRIB_CODENAME' not in release_info or
        'DISTRIB_DESCRIPTION' not in release_info or
        'DISTRIB_ID' not in release_info or
        'DISTRIB_RELEASE' not in release_info):
      return (None, None, None, None)
    return (release_info['DISTRIB_CODENAME'],
            release_info['DISTRIB_DESCRIPTION'],
            release_info['DISTRIB_ID'],
            release_info['DISTRIB_RELEASE'])

  def __init__(self):
    super(Ubuntu, self).__init__()
    (self.distribution_codename, _, self.distribution,
     self.distribution_version) = Ubuntu.ParseLsbRelease()
