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


"""SUSE Linux Enterprise (SLE) platform info."""

import re
from gcimagebundlelib import suse

class SLE(suse.SUSE):
  """SLE platform info."""

  @staticmethod
  def IsThisPlatform(self, root='/'):
    if re.match(r'SUSE Linux Enterprise', suse.SUSE().distribution):
      return True
    return False
  
  def __init__(self):
    super(SLE, self).__init__()

  def GetPreferredFilesystemType(self):
    return 'ext3'
