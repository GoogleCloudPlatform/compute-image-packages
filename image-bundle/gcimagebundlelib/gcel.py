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


"""GCE Linux specific platform info."""



import csv
import os

from gcimagebundlelib import linux


class Gcel(linux.LinuxPlatform):
  """GCE Linux specific information."""

  @staticmethod
  def IsThisPlatform(root='/'):
    release_file = root + '/etc/lsb-release'
    if os.path.exists(release_file):
      (flavor, _, _, _) = Gcel.ParseLsbRelease(release_file)
      if flavor and flavor.lower() == 'gcel':
        return True
    return False

  @staticmethod
  def ParseLsbRelease(release_file='/etc/lsb-release'):
    """Parses the /etc/lsb-releases file.

    Returns:
      A 4-tuple containing id, release, codename, and description
    """
    release_info = {}
    for line in csv.reader(open(release_file), delimiter='='):
      if len(line) > 1:
        release_info[line[0]] = line[1]
    return (release_info.get('DISTRIB_ID', None),
            release_info.get('DISTRIB_RELEASE', None),
            release_info.get('DISTRIB_CODENAME', None),
            release_info.get('DISTRIB_DESCRIPTION', None))

  def __init__(self):
    super(Gcel, self).__init__()
    (self.distribution, self.distribution_version,
     self.distribution_codename, _) = Gcel.ParseLsbRelease()
