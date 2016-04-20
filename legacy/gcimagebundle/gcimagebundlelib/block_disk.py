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

from gcimagebundlelib import exclude_spec
from gcimagebundlelib import fs_copy
from gcimagebundlelib import utils


class RawDiskError(Exception):
  """Error occured during raw disk creation."""


class InvalidRawDiskError(Exception):
  """Error when verification fails before copying."""


class FsRawDisk(fs_copy.FsCopy):
  """Creates a raw disk copy of OS image and bundles it into gzipped tar."""

  def __init__(self, fs_size, fs_type):
    """Constructor for FsRawDisk class.

    Args:
      fs_size: Size of the raw disk.
    """
    super(FsRawDisk, self).__init__()
    self._fs_size = fs_size
    self._fs_type = fs_type

  def _ResizeFile(self, file_path, file_size):
    logging.debug('Resizing %s to %s', file_path, file_size)
    with open(file_path, 'a') as disk_file:
      disk_file.truncate(file_size)

  def _InitializeDiskFileFromDevice(self, file_path):
    """Initializes disk file from the device specified in self._disk.

    It preserves whatever may be there on the device prior to the start of the
    first partition.

    At the moment this method supports devices with a single partition only.

    Args:
      file_path: The path where the disk file should be created.

    Returns:
      A tuple with partition_start, uuid. partition_start is the location
      where the first partition on the disk starts and uuid is the filesystem
      UUID to use for the first partition.

    Raises:
      RawDiskError: If there are more than one partition on the disk device.
    """
    # Find the disk size
    disk_size = utils.GetDiskSize(self._disk)
    logging.debug('Size of disk is %s', disk_size)
    # Make the disk file big enough to hold the disk
    self._ResizeFile(file_path, disk_size)
    # Find the location where the first partition starts
    partition_start = utils.GetPartitionStart(self._disk, 1)
    logging.debug('First partition starts at %s', partition_start)
    # Copy all the bytes as is from the start of the disk to the start of
    # first partition
    utils.CopyBytes(self._disk, file_path, partition_start)
    # Verify there is only 1 partition on the disk
    with utils.LoadDiskImage(file_path) as devices:
      # For now we only support disks with a single partition.
      if len(devices) == 0:
        raise RawDiskError(
            'Device %s should be a disk not a partition.' % self._disk)
      elif len(devices) != 1:
        raise RawDiskError(
            'Device %s has more than 1 partition. Only devices '
            'with a single partition are supported.' % self._disk)
    # Remove the first partition from the file we are creating. We will
    # recreate a partition that will fit inside _fs_size later.
    utils.RemovePartition(file_path, 1)
    # Resize the disk.raw file down to self._fs_size
    # We do this after removing the first partition to ensure that an
    # existing partition doesn't fall outside the boundary of the disk device.
    self._ResizeFile(file_path, self._fs_size)
    # Get UUID of the first partition on the disk
    # TODO(user): This is very hacky and relies on the disk path being
    # similar to /dev/sda etc which is bad. Need to fix it.
    uuid = utils.GetUUID(self._disk + '1')
    return partition_start, uuid

  def Bundleup(self):
    """Creates a raw disk copy of OS image and bundles it into gzipped tar.

    Returns:
      A size of a generated raw disk and the SHA1 digest of the the tar archive.

    Raises:
      RawDiskError: If number of partitions in a created image doesn't match
                    expected count.
    """

    # Create sparse file with specified size
    disk_file_path = os.path.join(self._scratch_dir, 'disk.raw')
    with open(disk_file_path, 'wb') as _:
      pass
    self._excludes.append(exclude_spec.ExcludeSpec(disk_file_path))

    logging.info('Initializing disk file')
    partition_start = None
    uuid = None
    if self._disk:
      # If a disk device has been provided then preserve whatever is there on
      # the disk before the first partition in case there is an MBR present.
      partition_start, uuid = self._InitializeDiskFileFromDevice(disk_file_path)
    else:
      # User didn't specify a disk device. Initialize a device with a simple
      # partition table.
      self._ResizeFile(disk_file_path, self._fs_size)
      # User didn't specify a disk to copy. Create a new partition table
      utils.MakePartitionTable(disk_file_path)
      # Pass 1MB as start to avoid 'Warning: The resulting partition is not
      # properly aligned for best performance.' from parted.
      partition_start = 1024 * 1024

    # Create a new partition starting at partition_start of size
    # self._fs_size - partition_start
    utils.MakePartition(disk_file_path, 'primary', 'ext2', partition_start,
                        self._fs_size - partition_start)
    with utils.LoadDiskImage(disk_file_path) as devices:
      # For now we only support disks with a single partition.
      if len(devices) != 1:
        raise RawDiskError(devices)
      # List contents of /dev/mapper to help with debugging. Contents will
      # be listed in debug log only
      utils.RunCommand(['ls', '/dev/mapper'])
      logging.info('Making filesystem')
      uuid = utils.MakeFileSystem(devices[0], self._fs_type, uuid)
    with utils.LoadDiskImage(disk_file_path) as devices:
      if uuid is None:
        raise Exception('Could not get uuid from MakeFileSystem')
      mount_point = tempfile.mkdtemp(dir=self._scratch_dir)
      with utils.MountFileSystem(devices[0], mount_point, self._fs_type):
        logging.info('Copying contents')
        self._CopySourceFiles(mount_point)
        self._CopyPlatformSpecialFiles(mount_point)
        self._ProcessOverwriteList(mount_point)
        self._CleanupNetwork(mount_point)
        self._UpdateFstab(mount_point, uuid)

    tar_entries = []

    manifest_file_path = os.path.join(self._scratch_dir, 'manifest.json')
    manifest_created = self._manifest.CreateIfNeeded(manifest_file_path)
    if manifest_created:
      tar_entries.append(manifest_file_path)

    tar_entries.append(disk_file_path)
    logging.info('Creating tar.gz archive')
    utils.TarAndGzipFile(tar_entries,
                         self._output_tarfile)
    for tar_entry in tar_entries:
      os.remove(tar_entry)

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
                      self._ignore_hard_links, recursive=True, xattrs=True)
          if dest:
            os.rename(os.path.join(mount_point, os.path.basename(src)),
                      os.path.join(mount_point, dest))
        else:
          utils.Rsync(src, os.path.join(mount_point, dest), rsync_file.name,
                      self._ignore_hard_links, recursive=False, xattrs=True)

  def _CopyPlatformSpecialFiles(self, mount_point):
    """Copies platform special files to a mounted raw disk.

    Args:
      mount_point: A path to a mounted raw disk.
    """
    if self._platform:
      special_files = self._platform.GetPlatformSpecialFiles(self._scratch_dir)
      for (src, dest) in special_files:
        # Ensure we don't use extended attributes here, so that copying /selinux
        # on Linux doesn't try and fail to preserve the SELinux context. That
        # doesn't work and causes rsync to return a nonzero status code.
        utils.Rsync(src, os.path.join(mount_point, dest), None,
                    self._ignore_hard_links, recursive=False, xattrs=False)

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
                      recursive=False, xattrs=True)


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
      logging.warning('etc/fstab does not exist.  Not updating fstab uuid')
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

    logging.debug('Original /etc/fstab contents:\n%s', lines)
    updated_lines = map(UpdateUUID, lines)
    if lines == updated_lines:
      logging.debug('No changes required to /etc/fstab')
      return
    logging.debug('Updated /etc/fstab contents:\n%s', updated_lines)
    f = open(fstab_path, 'w')
    f.write(''.join(updated_lines))
    f.close()


class RootFsRaw(FsRawDisk):
  """Block disk copy of the root file system.

  Takes care of additional checks for a root file system.
  """

  def __init__(
      self, fs_size, fs_type, skip_disk_space_check, statvfs = os.statvfs):
    # statvfs parameter is for unit test to mock out os.statvfs call.
    super(RootFsRaw, self).__init__(fs_size, fs_type)
    self._skip_disk_space_check = skip_disk_space_check
    self._statvfs = statvfs

  def _Verify(self):
    super(RootFsRaw, self)._Verify()
    # exactly one file system to bundle up
    if len(self._srcs) != 1:
      raise InvalidRawDiskError('Root filesystems must have exactly one src.')
    # check that destination field is empty.
    if self._srcs[0][1]:
      raise InvalidRawDiskError('Root filesystems must be copied as /')
    if (not self._skip_disk_space_check and
        self._srcs[0][0] == '/'):
      self._VerifyDiskSpace()

  def _VerifyDiskSpace(self):
    """Verify that there is enough free disk space to generate the image file"""
    # We use a very quick and simplistic check, 
    # DiskSpaceNeeded = disk.raw + image.tar.gz + LogFile
    # disk.raw = PartitionTable + AllFilesCopied
    # AllFilesCopied = RootDiskSize - RootDiskFreeSize - ExcludedFiles
    # We ignore LogFile, PartitionTable, and ExcludedFiles.
    # Some empirical experience showed that the compression ratio of the
    # tar.gz file is about 1/3. To be conservative, we assume image.tar.gz is
    # about 40% of disk.raw file.
    # As a result, DiskSpaceNeeded=1.4*(RootDiskSize - RootDiskFreeSize)
    # TODO(user): Make this check more accurate because ignoring ExcludedFiles 
    # can result in significant overestimation of disk
    # space needed if the user has large disk space used in /tmp, for example.
    root_fs = self._statvfs(self._srcs[0][0])
    disk_space_needed = long(1.4 * root_fs.f_bsize * (root_fs.f_blocks -
        root_fs.f_bfree))
    logging.info(("Root disk on %s: f_bsize=%d f_blocks=%d f_bfree=%d. "
                  "Estimated space needed is %d (may be overestimated)."), 
                 self._srcs[0][0], 
                 root_fs.f_bsize, 
                 root_fs.f_blocks,
                 root_fs.f_bfree,
                 disk_space_needed)

    # self._scratch_dir is where we will put the disk.raw and *.tar.gz file.
    scratch_fs = self._statvfs(self._scratch_dir)
    free_space = scratch_fs.f_bsize * scratch_fs.f_bfree
    logging.info("Free disk space for %s is %d bytes.", 
                 self._scratch_dir, 
                 free_space)

    if disk_space_needed > free_space:
      errorMessage = ("The operation may require up to %d bytes of disk space. "
        "However, the free disk space for %s is %d bytes.  Please consider "
        "freeing more disk space.  Note that the disk space required may "
        "be overestimated because it does not exclude temporary files that "
        "will not be copied.  You may use --skip_disk_space_check to disable "
        "this check.") % (disk_space_needed, self._scratch_dir, free_space)
      raise InvalidRawDiskError(errorMessage)
    if disk_space_needed > self._fs_size:
      errorMessage = ("The root disk files to be copied may require up to %d "
          "bytes. However, the limit on the image disk file is %d bytes.  "
          "Please consider deleting unused files from root disk, "
          "or increasing the image disk file limit with --fssize option.  "
          "Note that the disk space required may "
          "be overestimated because it does not exclude temporary files that "
          "will not be copied.  You may use --skip_disk_space_check to disable "
          "this check.") % (disk_space_needed, self._fs_size)
      raise InvalidRawDiskError(errorMessage)
    


