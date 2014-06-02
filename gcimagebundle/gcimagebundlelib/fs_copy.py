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


"""Creates a copy of specified directories\files."""



import logging
import os
import re

from gcimagebundlelib import manifest
from gcimagebundlelib import utils


class FsCopyError(Exception):
  """Error occured in fs copy operation."""


class InvalidFsCopyError(Exception):
  """Error when verification fails before fs copying."""


class FsCopy(object):
  """Specifies which files/directories must be copied."""

  def __init__(self):
    # Populate the required parameters with None so we can verify.
    self._output_tarfile = None
    self._srcs = []
    self._excludes = []
    self._key = None
    self._recursive = True
    self._fs_size = 0
    self._ignore_hard_links = False
    self._platform = None
    self._overwrite_list = []
    self._scratch_dir = '/tmp'
    self._disk = None
    self._manifest = manifest.ImageManifest(is_gce_instance=utils.IsRunningOnGCE())

  def SetTarfile(self, tar_file):
    """Sets tar file which will contain file system copy.

    Args:
      tar_file: path to a tar file.
    """
    self._output_tarfile = tar_file

  def AddDisk(self, disk):
    """Adds the disk which should be bundled.

    Args:
      disk: The block disk that needs to be bundled.
    """
    self._disk = disk

  def AddSource(self, src, arcname='', recursive=True):
    """Adds a source to be copied to the tar file.

    Args:
      src: path to directory/file to be copied.
      arcname: name of src in the tar archive. If arcname is empty, then instead
        of copying src itself only its content is copied.
      recursive: specifies if src directory should be copied recursively.

    Raises:
      ValueError: If src path doesn't exist.
    """
    if not os.path.exists(src):
      raise ValueError('invalid path')
    # Note that there is a fundamental asymmetry here as
    # abspath('/') => '/' while abspath('/usr/') => '/usr'.
    # This creates some subtleties elsewhere in the code.
    self._srcs.append((os.path.abspath(src), arcname, recursive))

  def AppendExcludes(self, excludes):
    """Adds a file/directory to be excluded from file copy.

    Args:
      excludes: A list of ExcludeSpec objects.
    """
    self._excludes.extend(excludes)

  def SetKey(self, key):
    """Sets a key to use to sign the archive digest.

    Args:
      key: key to use to sign the archive digest.
    """
    # The key is ignored for now.
    # TODO(user): sign the digest with the key
    self._key = key

  def SetPlatform(self, platform):
    """Sets the OS platform which is used to create an image.

    Args:
      platform: OS platform specific settings.
    """
    self._platform = platform
    logging.warning('overwrite list = %s',
                    ' '.join(platform.GetOverwriteList()))
    self._overwrite_list = [re.sub('^/', '', x)
                            for x in platform.GetOverwriteList()]

  def _SetManifest(self, image_manifest):
    """For test only, allows to set a test manifest object."""
    self._manifest = image_manifest

  def SetScratchDirectory(self, directory):
    """Sets a directory used for storing intermediate results.

    Args:
      directory: scratch directory path.
    """
    self._scratch_dir = directory

  def IgnoreHardLinks(self):
    """Requests that hard links should not be copied as hard links."""

    # TODO(user): I don't see a reason for this option to exist. Currently
    # there is a difference in how this option is interpreted between FsTarball
    # and FsRawDisk. FsTarball only copies one hard link to an inode and ignores
    # the rest of them. FsRawDisk copies the content of a file that hard link is
    # pointing to instead of recreating a hard link. Either option seems useless
    # for creating a copy of a file system.
    self._ignore_hard_links = True

  def Verify(self):
    """Verify if we have all the components to build a tar."""
    self._Verify()

  def Bundleup(self):
    """Creates the tar image based on set parameters.

    Returns:
      the SHA1 digest of the the tar archive.
    """
    return (0, None)

  def _Verify(self):
    """Verifies the tar attributes. Raises InvalidTarballError.

    Raises:
      InvalidFsCopyError: If not all required parameters are set.
      FsCopyError: If source file does not exist.
    """
    if not self._output_tarfile or not self._srcs or not self._key:
      raise InvalidFsCopyError('Incomplete copy spec')
    for (src, _, _) in self._srcs:
      if not os.path.exists(src):
        raise FsCopyError('%s does not exists' % src)

  def _ShouldExclude(self, filename):
    """"Checks if a file/directory are excluded from a copy.

    Args:
      filename: a file/directory path.

    Returns:
      True if a file/directory shouldn't be copied, False otherwise.
    """
    for spec in self._excludes:
      if spec.ShouldExclude(filename):
        logging.info('tarfile: Excluded %s', filename)
        return True
    return False
