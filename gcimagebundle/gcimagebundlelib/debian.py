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


"""Debian Linux specific platform info."""



import platform

from gcimagebundlelib import linux


class Debian(linux.LinuxPlatform):
  """Debian Linux specific information."""

  @staticmethod
  def IsThisPlatform(root='/'):
    (distribution, _, _) = platform.linux_distribution()
    if distribution and distribution.lower() == 'debian':
      return True
    return False

  def __init__(self):
    super(Debian, self).__init__()
