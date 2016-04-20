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


"""Base class for Linux platform specific information."""



import os
import platform
import stat

from gcimagebundlelib import exclude_spec
from gcimagebundlelib import os_platform


class LinuxPlatform(os_platform.Platform):
  """Base class for all Linux flavors."""
  EXCLUDE_LIST = [
      exclude_spec.ExcludeSpec('/etc/ssh/.host_key_regenerated'),
      exclude_spec.ExcludeSpec('/dev', preserve_dir=True),
      exclude_spec.ExcludeSpec('/proc', preserve_dir=True),
      exclude_spec.ExcludeSpec('/run',
                               preserve_dir=True, preserve_subdir=True),
      exclude_spec.ExcludeSpec('/selinux'),
      exclude_spec.ExcludeSpec('/tmp', preserve_dir=True),
      exclude_spec.ExcludeSpec('/sys', preserve_dir=True),
      exclude_spec.ExcludeSpec('/var/lib/google/per-instance',
                               preserve_dir=True),
      exclude_spec.ExcludeSpec('/var/lock',
                               preserve_dir=True, preserve_subdir=True),
      exclude_spec.ExcludeSpec('/var/log',
                               preserve_dir=True, preserve_subdir=True),
      exclude_spec.ExcludeSpec('/var/run',
                               preserve_dir=True, preserve_subdir=True)]

  def __init__(self):
    """Populate the uname -a information."""
    super(LinuxPlatform, self).__init__()
    (self.name, self.hostname, self.release, self.version, self.architecture,
     self.processor) = platform.uname()
    (self.distribution, self.distribution_version,
     self.distribution_codename) = platform.dist()

  def GetPlatformDetails(self):
    return ' '.join([self.name, self.hostname, self.release, self.version,
                     self.architecture, self.processor, self.distribution,
                     self.distribution_version, self.distribution_codename])

  def GetName(self):
    return self.GetOs()

  def GetProcessor(self):
    return platform.processor()

  def GetArchitecture(self):
    if self.architecture:
      return self.architecture
    return ''

  def GetOs(self):
    if self.distribution:
      if self.distribution_codename:
        return '%s (%s)' % (self.distribution, self.distribution_codename)
      else:
        return self.distribution
    if self.name:
      return self.name
    return 'Linux'

  def IsLinux(self):
    return True

  # Linux specific methods
  def GetKernelVersion(self):
    return self.release

  # distribution specific methods
  # if platforms module does not do a good job override these.
  def GetDistribution(self):
    return self.distribution

  def GetDistributionCodeName(self):
    return self.distribution_codename

  def GetDistributionVersion(self):
    return self.distribution_version

  def GetPlatformSpecialFiles(self, tmpdir='/tmp'):
    """Creates any platform specific special files."""
    retval = []
    console_dev = os.makedev(5, 1)
    os.mknod(tmpdir + 'console', stat.S_IFCHR |
             stat.S_IRUSR | stat.S_IWUSR, console_dev)
    retval.append((tmpdir + 'console', 'dev/console'))
    null_dev = os.makedev(1, 3)
    os.mknod(tmpdir + 'null', stat.S_IFCHR |
             stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IWGRP |
             stat.S_IROTH | stat.S_IWOTH, null_dev)
    retval.append((tmpdir + 'null', 'dev/null'))
    tty_dev = os.makedev(5, 0)
    os.mknod(tmpdir + 'tty', stat.S_IFCHR |
             stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IWGRP |
             stat.S_IROTH | stat.S_IWOTH, tty_dev)
    retval.append((tmpdir + 'tty', 'dev/tty'))
    zero_dev = os.makedev(1, 5)
    os.mknod(tmpdir + 'zero', stat.S_IFCHR |
             stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IWGRP |
             stat.S_IROTH | stat.S_IWOTH, zero_dev)
    retval.append((tmpdir + 'zero', 'dev/zero'))
    # /selinux is deprecated in favor of /sys/fs/selinux, but preserve it on
    # those OSes where it's present.
    if os.path.isdir('/selinux'):
      os.mkdir(tmpdir + 'selinux', 0755)
      retval.append((tmpdir + 'selinux', 'selinux'))
    return retval

  def Overwrite(self, filename, arcname, tmpdir='/tmp'):
    """Overwrites specified file if needed for the Linux platform."""
    pass

  def GetPreferredFilesystemType(self):
    """Return the optimal filesystem supported for the platform."""
    return 'ext4'
