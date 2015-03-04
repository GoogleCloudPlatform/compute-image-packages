"""Gentoo specific platform info."""



import os
import platform

from gcimagebundlelib import linux


class Gentoo(linux.LinuxPlatform):
  """Gentoo specific information."""

  @staticmethod
  def IsThisPlatform(root='/'):
    release_file = root + '/etc/gentoo-release'
    if os.path.exists(release_file):
      return True
    return False

  def __init__(self):
    super(Gentoo, self).__init__()

  def GetPreferredFilesystemType(self):
    return 'ext4'