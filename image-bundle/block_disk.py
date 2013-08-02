#!/usr/bin/python
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

"""Module to create raw disk images.

Stores a copy of directories/files in a file mounted as a partitioned blocked
device.
"""



import hashlib
import logging
import os
import re
import tempfile

import exclude_spec
import fs_copy
import utils


class RawDiskError(Exception):
  """Error occured during raw disk creation."""


class InvalidRawDiskError(Exception):
  """Error when verification fails before copying."""


class FsRawDisk(fs_copy.FsCopy):
  """Creates a raw disk copy of OS image and bundles it into gzipped tar."""

  def __init__(self, fs_size):
    """Constructor for FsRawDisk class.

    Args:
      fs_size: Size of the raw disk.
    """
    super(FsRawDisk, self).__init__()
    self._fs_size = fs_size

  def Bundleup(self):
    """Creates a raw disk copy of OS image and bundles it into gzipped tar.

    Returns:
      A size of a generated raw disk and the SHA1 digest of the the tar archive.

    Raises:
      RawDiskError: If number of partitions in a created image doesn't match
                    expected count.
    """
    self._Verify()
    # Create sparse file with specified size
    file_path = os.path.join(self._scratch_dir, 'disk.raw')
    self._excludes.append(exclude_spec.ExcludeSpec(file_path))
    with open(file_path, 'wb') as disk_file:
      disk_file.truncate(self._fs_size)
    utils.MakePartitionTable(file_path)
    # Pass 1MB as start to avoid 'Warning: The resulting partition is not
    # properly aligned for best performance.' from parted.
    utils.MakePartition(file_path, 'primary', 'ext2', 1024 * 1024,
                        self._fs_size)
    with utils.LoadDiskImage(file_path) as devices:
      # For now we only support disks with a single partition.
      if len(devices) != 1:
        raise RawDiskError(devices)
      uuid = utils.MakeFileSystem(devices[0], 'ext4')
      if uuid is None:
        raise Exception('Could not get uuid from makefilesystem')
      mount_point = tempfile.mkdtemp(dir=self._scratch_dir)
      with utils.MountFileSystem(devices[0], mount_point):
        self._CopySourceFiles(mount_point)
        self._CopyPlatformSpecialFiles(mount_point)
        self._ProcessOverwriteList(mount_point)
        self._CleanupNetwork(mount_point)
        self._UpdateFstab(mount_point, uuid)

    utils.TarAndGzipFile(file_path, self._output_tarfile)
    os.remove(file_path)
    # TODO(user): It would be better to compute tar.gz file hash during
    # archiving.
    h = hashlib.sha1()
    with open(self._output_tarfile, 'rb') as tar_file:
      for chunk in iter(lambda: tar_file.read(8192), ''):
        h.update(chunk)
    return (self._fs_size, h.hexdigest())

  def _CopySourceFiles(self, mount_point):
    """Copies all source files/directories to a mounted raw disk.

    There are several cases which must be handled separately:
      1. src=dir1 and dest is empty. In this case we simply copy the content of
        dir1 to mount_point.
      2. src=dir1 and dest=dir2. In this case dir1 is copied to mount_point
        under a new name dir2, so its content would be copied under
        mount_point/dir2.
      3. src=file1/dir1 and dest=file2/dir2 and is_recursive=False. file1/dir1
        is copied to mount_point/file2 or mount_point/dir2.

    Args:
      mount_point: A path to a mounted raw disk.
    """
    for (src, dest, is_recursive) in self._srcs:
      # Generate a list of files/directories excluded from copying to raw disk.
      # rsync expects them to be relative to src directory so we need to
      # regenerate this list for every src separately.
      with tempfile.NamedTemporaryFile(dir=self._scratch_dir) as rsync_file:
        for spec in self._excludes:
          rsync_file.write(spec.GetRsyncSpec(src))

        # make sure that rsync utility sees all the content of rsync_file which
        # otherwise can be buffered.
        rsync_file.flush()
        if is_recursive:
          # if a directory ends with / rsync copies the content of a
          # directory, otherwise it also copies the directory itself.
          src = src.rstrip('/')
          if not dest:
            src += '/'
          utils.Rsync(src, mount_point, rsync_file.name,
                      self._ignore_hard_links, recursive=True)
          if dest:
            os.rename(os.path.join(mount_point, os.path.basename(src)),
                      os.path.join(mount_point, dest))
        else:
          utils.Rsync(src, os.path.join(mount_point, dest), rsync_file.name,
                      self._ignore_hard_links, recursive=False)

  def _CopyPlatformSpecialFiles(self, mount_point):
    """Copies platform special files to a mounted raw disk.

    Args:
      mount_point: A path to a mounted raw disk.
    """
    if self._platform:
      special_files = self._platform.GetPlatformSpecialFiles(self._scratch_dir)
      for (src, dest) in special_files:
        utils.Rsync(src, os.path.join(mount_point, dest), None,
                    self._ignore_hard_links, recursive=False)

  def _ProcessOverwriteList(self, mount_point):
    """Overwrites a set of files/directories requested by platform.

    Args:
      mount_point: A path to a mounted raw disk.
    """
    for file_name in self._overwrite_list:
      file_path = os.path.join(mount_point, file_name)
      if os.path.exists(file_path):
        if os.path.isdir(file_path):
          # TODO(user): platform.Overwrite is expected to overwrite the
          # directory in place from what I can tell. In case of a file it will
          # create a new file which must be copied to mounted raw disk. So there
          # some inconsistency which would need to be addresses if and when we
          # encounter a platform which would want to overwrite a directory.
          self._platform.Overwrite(file_path, file_name, self._scratch_dir)
          logging.info('rawdisk: modifying directory %s', file_path)
        else:
          new_file = self._platform.Overwrite(file_path, file_name,
                                              self._scratch_dir)
          logging.info('rawdisk: modifying %s from %s', file_path, new_file)
          utils.Rsync(new_file, file_path, None, self._ignore_hard_links,
                      recursive=False)


  def _CleanupNetwork(self, mount_point):
    """Remove any record of our current MAC address."""
    net_rules_path = os.path.join(
        mount_point,
        'lib/udev/rules.d/75-persistent-net-generator.rules')
    if os.path.exists(net_rules_path):
      os.remove(net_rules_path)

  def _UpdateFstab(self, mount_point, uuid):
    """Update /etc/fstab with the new root fs UUID."""
    fstab_path = os.path.join(mount_point, 'etc/fstab')
    if not os.path.exists(fstab_path):
      print 'etc/fstab does not exist.  Not updating fstab uuid'
      return

    f = open(fstab_path, 'r')
    lines = f.readlines()
    f.close()

    def UpdateUUID(line):
      """Replace the UUID on the entry for /."""
      g = re.match(r'UUID=\S+\s+/\s+(.*)', line)
      if not g:
        return line
      return 'UUID=%s / %s\n' % (uuid, g.group(1))

    lines = map(UpdateUUID, lines)
    f = open(fstab_path, 'w')
    f.write(''.join(lines))
    f.close()


class RootFsRaw(FsRawDisk):
  """Block disk copy of the root file system.

  Takes care of additional checks for a root file system.
  """

  def __init__(self, fs_size):
    super(RootFsRaw, self).__init__(fs_size)

  def _Verify(self):
    super(RootFsRaw, self)._Verify()
    # exactly one file system to bundle up
    if len(self._srcs) != 1:
      raise InvalidRawDiskError('Root filesystems must have exactly one src.')
    # check that destination field is empty.
    if self._srcs[0][1]:
      raise InvalidRawDiskError('Root filesystems must be copied as /')
