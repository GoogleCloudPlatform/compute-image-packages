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


"""Centos specific platform info."""



import os
import platform
import re

from gcimagebundlelib import linux


class Centos(linux.LinuxPlatform):
  """Centos specific information."""

  @staticmethod
  def IsThisPlatform(root='/'):
    release_file = root + '/etc/redhat-release'
    if os.path.exists(release_file):
      (_, _, flavor, _) = Centos.ParseRedhatRelease(release_file)
      if flavor and flavor.lower() == 'centos':
        return True
    return False

  @staticmethod
  def ParseRedhatRelease(release_file='/etc/redhat-release'):
    """Parses the /etc/redhat-release file."""
    f = open(release_file)
    lines = f.readlines()
    f.close()
    if not lines:
      return (None, None, None, None)
    line0 = lines[0]
    # Matches both CentOS 6 and CentOS 7 formats.
    # CentOS 6: CentOS release 6.5 (Final)
    # CentOS 7: CentOS Linux release 7.0.1406 (Core)
    g = re.match(r'(\S+)( Linux)? release (\d+(\.\d+)+) \(([^)]*)\)', line0)
    if not g:
      return (None, None, None, None)
    (osname, version, label) = (g.group(1), g.group(3), g.group(5))
    return (osname, label, osname, version)

  def __init__(self):
    super(Centos, self).__init__()
    (self.distribution_codename, _, self.distribution,
     self.distribution_version) = Centos.ParseRedhatRelease()

  def GetPreferredFilesystemType(self):
    (_,version,_) = platform.linux_distribution()
    if version.startswith('7'):
      return 'xfs'
    return 'ext4'
