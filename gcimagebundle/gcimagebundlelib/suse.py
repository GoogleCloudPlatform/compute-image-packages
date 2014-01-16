# Copyright 2013 SUSE LLC All Rights Reserved
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


"""openSUSE and SUSE generic platform info."""

import os
import re

from gcimagebundlelib import linux


class SUSE(linux.LinuxPlatform):
  """openSUSE and SUSE generic platform info."""

  def __init__(self):
    super(SUSE, self).__init__()
    self.distribution_codename = None
    self.ParseOSRelease()
    if not self.distribution:
      self.ParseSUSERelease()
    if not self.distribution:
      self.distribution = ''

  def ParseOSRelease(self):
    """Parse the /etc/os-release file."""
    release_file = '/etc/os-release'
    if not os.path.isfile(release_file):
      self.distribution = None
      return
    lines = open(release_file, 'r').readlines()
    for ln in lines:
      if not ln:
        continue
      if re.match(r'^NAME=', ln):
        self.distribution = self.__getData(ln)
      if re.match(r'^VERSION_ID=', ln):
        self.distribution_version = self.__getData(ln)
      if re.match(r'^VERSION=', ln):
        data = self.__getData(ln)
        self.distribution_codename = data.split('(')[-1][:-1]
    return

  def ParseSUSERelease(self):
    """Parse /etc/SuSE-release file."""
    release_file = '/etc/SuSE-release'
    if not os.path.isfile(release_file):
      self.distribution = None
      return
    lines = open(release_file, 'r').readlines()
    prts = lines[0].split()
    cnt = 0
    self.distribution = ''
    if len(prts):
      while 1:
        item = prts[cnt]
        if re.match('\d', item):
          item = None
          break
        elif cnt > 0:
          self.distribution += ' '              
        self.distribution += item
        cnt += 1

    for ln in lines:
      if re.match(r'^VERSION =', ln):
        self.distribution_version = self.__getData(ln)
      if re.match(r'^CODENAME =', ln):
        self.distribution_codename = self.__getData(ln)
    return

  def __getData(self, ln):
    """Extract data from a line in a file. Either returns data inside the
       first double quotes ("a b"; a b in this example) or if no double
       quotes exist, returns the data after the first = sign. Leading
       and trailing whitspace are stripped."""
    if ln.find('"') != -1:
      return ln.split('"')[1]
    else:
      return ln.split('=')[-1].strip()
