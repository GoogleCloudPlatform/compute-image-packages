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


"""Base class for platform specific information."""


class Platform(object):
  """Base class for platform information."""
  EXCLUDE_LIST = []
  OVERWRITE_LIST = []

  @staticmethod
  def IsThisPlatform(root='/'):
    return False

  def __init__(self):
    pass

  def GetName(self):
    """Generic name for the platform."""
    return 'Unknown'

  def GetProcessor(self):
    """Real processor."""
    return ''

  def GetArchitecture(self):
    """Returns machine architecture."""
    return ''

  def GetExcludeList(self):
    """Returns the default exclude list of the platform."""
    return self.__class__.EXCLUDE_LIST

  def GetOs(self):
    """Returns the name of OS."""
    return 'Unknown'

  def IsLinux(self):
    return False

  def IsWindows(self):
    return False

  def IsUnix(self):
    return False

  def GetOverwriteList(self):
    """Returns list of platform specific files to overwrite."""
    return self.__class__.OVERWRITE_LIST

  def Overwrite(self, file_path, file_name, scratch_dir):
    """Called for each file in the OverwriteList."""
    return file_name

  def GetPlatformSpecialFiles(self, tmpdir):
    """returns a list of platform special files that should be created."""
    return []
