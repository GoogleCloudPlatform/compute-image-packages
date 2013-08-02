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


"""Utilities for image bundling tool."""



import logging
import os
import subprocess
import time


class MakePartitionTableException(Exception):
  """Error occurred in parted during partition table creation."""


class MakePartitionException(Exception):
  """Error occurred in parted during partition creation."""


class LoadDiskImageException(Exception):
  """Error occurred in kpartx loading a raw image."""


class MakeFileSystemException(Exception):
  """Error occurred in file system creation."""


class MountFileSystemException(Exception):
  """Error occurred in file system mount."""


class RsyncException(Exception):
  """Error occurred in rsync execution."""


class TarAndGzipFileException(Exception):
  """Error occurred in tar\gzip execution."""


class LoadDiskImage(object):
  """Loads raw disk image using kpartx."""

  def __init__(self, file_path):
    """Initializes LoadDiskImage object.

    Args:
      file_path: a path to a file containing raw disk image.

    Raises:
      LoadDiskImageException: If kpartx encountered an error while load image.

    Returns:
      A list of devices for every partition found in an image.
    """
    self._file_path = file_path

  def __enter__(self):
    """Map disk image as a device."""
    kpartx_cmd = ['kpartx', '-av', self._file_path]
    p = subprocess.Popen(kpartx_cmd, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    output = p.communicate()[0]
    if p.returncode != 0:
      raise LoadDiskImageException(output)
    devs = []
    for line in output.splitlines():
      split_line = line.split()
      if (len(split_line) > 2 and split_line[0] == 'add'
          and split_line[1] == 'map'):
        devs.append('/dev/mapper/' + split_line[2])
    return devs

  def __exit__(self, unused_exc_type, unused_exc_value, unused_exc_tb):
    """Unmap disk image as a device.

    Args:
      unused_exc_type: unused.
      unused_exc_value: unused.
      unused_exc_tb: unused.
    """
    kpartx_cmd = ['kpartx', '-d', self._file_path]
    subprocess.call(kpartx_cmd)


class MountFileSystem(object):
  """Mounts a file system."""

  def __init__(self, dev_path, dir_path):
    """Initializes MountFileSystem object.

    Args:
      dev_path: A path to a device to mount.
      dir_path: A path to a directory where a device is to be mounted.
    """
    self._dev_path = dev_path
    self._dir_path = dir_path

  def __enter__(self):
    """Mounts a device.

    Raises:
      MakeFileSystemException: If a mount command encountered an error.
    """
    mount_cmd = ['mount', self._dev_path, self._dir_path]
    retcode = subprocess.call(mount_cmd)
    if retcode != 0:
      raise MakeFileSystemException(self._dev_path)

  def __exit__(self, unused_exc_type, unused_exc_value, unused_exc_tb):
    """Unmounts a file system.

    Args:
      unused_exc_type: unused.
      unused_exc_value: unused.
      unused_exc_tb: unused.
    """
    umount_cmd = ['umount', self._dir_path]
    subprocess.call(umount_cmd)


def GetMounts(root='/'):
  """Find all mount points under the specified root.

  Args:
    root: a path to look for a mount points.

  Returns:
    A list of mount points.
  """
  mount_cmd = ['/bin/mount', '-l']
  output = subprocess.Popen(mount_cmd, stdout=subprocess.PIPE).communicate()[0]
  mounts = []
  for line in output.splitlines():
    split_line = line.split()
    mount_point = split_line[2]
    if mount_point == root:
      continue
    # We are simply ignoring the fs_type of fs for now. But we can use that
    # later Just verify that these are actually mount points.
    if os.path.ismount(mount_point) and mount_point.startswith(root):
      mounts.append(mount_point)
  return mounts


def MakePartitionTable(file_path):
  """Create a partition table in a file.

  Args:
    file_path: A path to a file where a partition table will be created.

  Raises:
    MakePartitionTableException: If parted encounters an error.
  """
  parted_cmd = ['parted', file_path, 'mklabel', 'msdos']
  retcode = subprocess.call(parted_cmd)
  if retcode != 0:
    raise MakePartitionTableException(file_path)


def MakePartition(file_path, partition_type, fs_type, start, end):
  """Create a partition in a file.

  Args:
    file_path: A path to a file where a partition will be created.
    partition_type: A type of a partition to be created. Tested option is msdos.
    fs_type: A type of a file system to be created. For example, ext2, ext3,
      etc.
    start: Start offset of a partition in bytes.
    end: End offset of a partition in bytes.

  Raises:
    MakePartitionException: If parted encounters an error.
  """
  parted_cmd = ['parted', file_path, 'mkpart', partition_type, fs_type,
                str(start / (1024 * 1024)), str(end / (1024 * 1024))]
  retcode = subprocess.call(parted_cmd)
  if retcode != 0:
    raise MakePartitionException(file_path)


def MakeFileSystem(dev_path, fs_type):
  """Create a file system in a device.

  Args:
    dev_path: A path to a device.
    fs_type: A type of a file system to be created. For example ext2, ext3, etc.

  Returns:
    The uuid of the filesystem.

  Raises:
    MakeFileSystemException: If mkfs encounters an error.
  """
  p = subprocess.Popen(['uuidgen'], stdout=subprocess.PIPE)
  if p.wait() != 0:
    raise MakeFileSystemException(dev_path)
  uuid = p.communicate()[0].strip()
  if uuid is None:
    raise MakeFileSystemException(dev_path)

  mkfs_cmd = ['mkfs', '-t', fs_type, dev_path]
  retcode = subprocess.call(mkfs_cmd)
  if retcode != 0:
    raise MakeFileSystemException(dev_path)

  set_uuid_cmd = ['tune2fs', '-U', uuid, dev_path]
  retcode = subprocess.call(set_uuid_cmd)
  if retcode != 0:
    raise MakeFileSystemException(dev_path)

  return uuid


def Rsync(src, dest, exclude_file, ignore_hard_links, recursive):
  """Copy files from specified directory using rsync.

  Args:
    src: Source location to copy.
    dest: Destination to copy files to.
    exclude_file: A path to a file which contains a list of exclude from copy
      filters.
    ignore_hard_links: If True a hard links are copied as a separate files. If
      False, hard link are recreated in dest.
    recursive: Specifies if directories are copied recursively or not.

  Raises:
    RsyncException: If rsync encounters an error.
  """
  rsync_cmd = ['rsync', '--times', '--perms', '--owner', '--group', '--links',
               '--devices', '--sparse']
  if not ignore_hard_links:
    rsync_cmd.append('--hard-links')
  if recursive:
    rsync_cmd.append('--recursive')
  else:
    rsync_cmd.append('--dirs')
  if exclude_file:
    rsync_cmd.append('--exclude-from=' + exclude_file)
  rsync_cmd.extend([src, dest])

  logging.debug('Calling: %s', repr(rsync_cmd))
  if exclude_file:
    logging.debug('Contents of exclude file %s:', exclude_file)
    with open(exclude_file, 'rb') as excludes:
      for line in excludes:
        logging.debug('  %s', line.rstrip())

  # TODO: It would be great to capture the stderr/stdout from this and
  # put it in the log.  We could then include verbose output.
  retcode = subprocess.call(rsync_cmd)
  if retcode != 0:
    raise RsyncException(src)


def TarAndGzipFile(src, dest):
  """Pack file in tar archive and optionally gzip it.

  Args:
    src: A file to archive.
    dest: An archive name. If a file ends with .gz or .tgz an archive is gzipped
      as well.

  Raises:
    TarAndGzipFileException: If tar encounters an error.
  """
  if dest.endswith('.gz') or dest.endswith('.tgz'):
    mode = 'czSf'
  else:
    mode = 'cSf'
  tar_cmd = ['tar', mode, dest, '-C', os.path.dirname(src),
             os.path.basename(src)]
  retcode = subprocess.call(tar_cmd)
  if retcode != 0:
    raise TarAndGzipFileException(src)
