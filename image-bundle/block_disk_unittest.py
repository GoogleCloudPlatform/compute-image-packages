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

"""Unittest for block_disk.py module."""


__pychecker__ = 'no-local'  # for unittest


import logging
import os
import subprocess
import tempfile
import unittest

import block_disk
import exclude_spec
import image_bundle_test_base
import utils


class FsRawDiskTest(image_bundle_test_base.ImageBundleTest):
  """FsRawDisk Unit Test."""

  def setUp(self):
    super(FsRawDiskTest, self).setUp()
    self._bundle = block_disk.FsRawDisk(10*1024*1024)
    self._tar_path = self.tmp_path + '/image.tar.gz'
    self._bundle.SetTarfile(self._tar_path)
    self._bundle.AppendExcludes([exclude_spec.ExcludeSpec(self._tar_path)])
    self._bundle.SetKey('key')

  def tearDown(self):
    super(FsRawDiskTest, self).tearDown()

  def testRawDisk(self):
    """Tests the regular operation. No expected error."""
    self._bundle.AddSource(self.tmp_path)
    self._bundle.Verify()
    (_, digest) = self._bundle.Bundleup()
    if not digest:
      self.fail('raw disk failed')
    self._VerifyTarHas(self._tar_path, ['disk.raw'])
    self._VerifyImageHas(self._tar_path,
                         ['lost+found', 'test1', 'test2', 'dir1/',
                          '/dir1/dir11/', '/dir1/sl1', '/dir1/hl2', 'dir2/',
                          '/dir2/dir1', '/dir2/sl2', '/dir2/hl1'])
    self._VerifyNumberOfHardLinksInRawDisk(self._tar_path, 'test1', 2)
    self._VerifyNumberOfHardLinksInRawDisk(self._tar_path, 'test2', 2)

  def testRawDiskIgnoresHardlinks(self):
    """Tests if the raw disk ignores hard links if asked."""
    self._bundle.AddSource(self.tmp_path)
    self._bundle.IgnoreHardLinks()
    self._bundle.Verify()
    (_, digest) = self._bundle.Bundleup()
    if not digest:
      self.fail('raw disk failed')
    self._VerifyTarHas(self._tar_path, ['disk.raw'])
    self._VerifyImageHas(self._tar_path,
                         ['lost+found', 'test1', 'test2', 'dir1/',
                          '/dir1/dir11/', '/dir1/sl1', '/dir1/hl2', 'dir2/',
                          '/dir2/dir1', '/dir2/sl2', '/dir2/hl1'])
    self._VerifyNumberOfHardLinksInRawDisk(self._tar_path, 'test1', 1)
    self._VerifyNumberOfHardLinksInRawDisk(self._tar_path, 'test2', 1)

  def testRawDiskIgnoresExcludes(self):
    """Tests if the raw disk ignores specified excludes files."""
    self._bundle.AddSource(self.tmp_path)
    self._bundle.AppendExcludes(
        [exclude_spec.ExcludeSpec(self.tmp_path + '/dir1')])
    self._bundle.Verify()
    (_, digest) = self._bundle.Bundleup()
    if not digest:
      self.fail('raw disk failed')
    self._VerifyTarHas(self._tar_path, ['disk.raw'])
    self._VerifyImageHas(self._tar_path,
                         ['lost+found', 'test1', 'test2', 'dir2/', '/dir2/dir1',
                          '/dir2/sl2', '/dir2/hl1'])

  def testRawDiskExcludePreservesSubdirs(self):
    """Tests if excludes preserves subdirs underneath if asked."""
    self._bundle.AddSource(self.tmp_path)
    self._bundle.AppendExcludes(
        [exclude_spec.ExcludeSpec(self.tmp_path + '/dir1',
                                  preserve_dir=True,
                                  preserve_subdir=True)])
    self._bundle.Verify()
    (_, digest) = self._bundle.Bundleup()
    if not digest:
      self.fail('raw disk failed')
    self._VerifyTarHas(self._tar_path, ['disk.raw'])
    self._VerifyImageHas(self._tar_path,
                         ['lost+found', 'test1', 'test2', 'dir1/',
                          '/dir1/dir11', 'dir2/', '/dir2/dir1',
                          '/dir2/sl2', '/dir2/hl1'])

  def testRawDiskExcludePreservesFiles(self):
    """Tests if excludes preserves the files underneath if asked."""
    self._bundle.AddSource(self.tmp_path)
    self._bundle.AppendExcludes(
        [exclude_spec.ExcludeSpec(self.tmp_path + '/dir1',
                                  preserve_dir=True,
                                  preserve_file=True)])
    self._bundle.Verify()
    (_, digest) = self._bundle.Bundleup()
    if not digest:
      self.fail('raw disk failed')
    self._VerifyTarHas(self._tar_path, ['disk.raw'])
    self._VerifyImageHas(self._tar_path,
                         ['lost+found', 'test1', 'test2', 'dir1/', '/dir1/hl2',
                          '/dir1/sl1', 'dir2/', '/dir2/dir1', '/dir2/sl2',
                          '/dir2/hl1'])

  def testRawDiskUsesModifiedFiles(self):
    """Tests if the raw disk uses modified files."""
    self._bundle.AddSource(self.tmp_path)
    self._bundle.AppendExcludes(
        [exclude_spec.ExcludeSpec(self.tmp_path + '/dir1')])
    self._bundle.SetPlatform(image_bundle_test_base.MockPlatform(self.tmp_root))
    self._bundle.Verify()
    (_, digest) = self._bundle.Bundleup()
    if not digest:
      self.fail('raw disk failed')
    self._VerifyTarHas(self._tar_path, ['disk.raw'])
    self._VerifyImageHas(self._tar_path,
                         ['lost+found', 'test1', 'test2', 'dir2/',
                          '/dir2/dir1', '/dir2/sl2', '/dir2/hl1'])
    self._VerifyFileInRawDiskEndsWith(self._tar_path, 'test1',
                                      'something extra.')

  def testRawDiskGeneratesCorrectDigest(self):
    """Tests if the SHA1 digest generated is accurate."""
    self._bundle.AddSource(self.tmp_path)
    self._bundle.Verify()
    (_, digest) = self._bundle.Bundleup()
    if not digest:
      self.fail('raw disk failed')
    p = subprocess.Popen(['/usr/bin/openssl dgst -sha1 ' + self._tar_path],
                         stdout=subprocess.PIPE, shell=True)
    file_digest = p.communicate()[0].split('=')[1].strip()
    self.assertEqual(digest, file_digest)

  def testRawDiskHonorsRecursiveOff(self):
    """Tests if raw disk handles recursive off."""
    self._bundle.AppendExcludes([exclude_spec.ExcludeSpec(self._tar_path)])
    self._bundle.AddSource(self.tmp_path + '/dir1',
                           arcname='dir1', recursive=False)
    self._bundle.AddSource(self.tmp_path + '/dir2', arcname='dir2')
    self._bundle.Verify()
    (_, digest) = self._bundle.Bundleup()
    if not digest:
      self.fail('raw disk failed')
    self._VerifyTarHas(self._tar_path, ['disk.raw'])
    self._VerifyImageHas(self._tar_path,
                         ['lost+found', 'dir1/', 'dir2/', '/dir2/dir1',
                          '/dir2/sl2', '/dir2/hl1'])

  def _VerifyImageHas(self, tar, expected):
    """Tests if raw disk contains an expected list of files/directories."""
    tmp_dir = tempfile.mkdtemp(dir='/tmp')
    tar_cmd = ['tar', '-xzf', tar, '-C', tmp_dir]
    self.assertEqual(subprocess.call(tar_cmd), 0)
    disk_path = os.path.join(tmp_dir, 'disk.raw')
    with utils.LoadDiskImage(disk_path) as devices:
      self.assertEqual(len(devices), 1)
      mnt_dir = tempfile.mkdtemp(dir='/tmp')
      with utils.MountFileSystem(devices[0], mnt_dir):
        found = []
        for root, dirs, files in os.walk(mnt_dir):
          root = root.replace(mnt_dir, '')
          for f in files:
            found.append(os.path.join(root, f))
          for d in dirs:
            found.append(os.path.join(root, d))
    self._AssertListEqual(expected, found)

  def _VerifyFileInRawDiskEndsWith(self, tar, filename, text):
    """Tests if a file on raw disk contains ends with a specified text."""
    tmp_dir = tempfile.mkdtemp(dir='/tmp')
    tar_cmd = ['tar', '-xzf', tar, '-C', tmp_dir]
    self.assertEqual(subprocess.call(tar_cmd), 0)
    disk_path = os.path.join(tmp_dir, 'disk.raw')
    with utils.LoadDiskImage(disk_path) as devices:
      self.assertEqual(len(devices), 1)
      mnt_dir = tempfile.mkdtemp(dir='/tmp')
      with utils.MountFileSystem(devices[0], mnt_dir):
        f = open(os.path.join(mnt_dir, filename), 'r')
        file_content = f.read()
        f.close()
        self.assertTrue(file_content.endswith(text))

  def _VerifyNumberOfHardLinksInRawDisk(self, tar, filename, count):
    """Tests if a file on raw disk has a specified number of hard links."""
    tmp_dir = tempfile.mkdtemp(dir='/tmp')
    tar_cmd = ['tar', '-xzf', tar, '-C', tmp_dir]
    self.assertEqual(subprocess.call(tar_cmd), 0)
    disk_path = os.path.join(tmp_dir, 'disk.raw')
    with utils.LoadDiskImage(disk_path) as devices:
      self.assertEqual(len(devices), 1)
      mnt_dir = tempfile.mkdtemp(dir='/tmp')
      with utils.MountFileSystem(devices[0], mnt_dir):
        self.assertEqual(os.stat(os.path.join(mnt_dir, filename)).st_nlink,
                         count)


class RootFsRawTest(image_bundle_test_base.ImageBundleTest):
  """RootFsRaw Unit Test."""

  def setUp(self):
    super(RootFsRawTest, self).setUp()
    self._bundle = block_disk.RootFsRaw(10*1024*1024)
    self._tar_path = self.tmp_path + '/image.tar.gz'
    self._bundle.SetTarfile(self._tar_path)
    self._bundle.AppendExcludes([exclude_spec.ExcludeSpec(self._tar_path)])

  def tearDown(self):
    super(RootFsRawTest, self).tearDown()

  def testRootRawDiskVerifiesOneSource(self):
    """Tests that only one root directory is allowed."""
    self._bundle.AddSource(self.tmp_path)
    self._bundle.AddSource(self.tmp_path + '/dir1')
    self._bundle.SetKey('key')
    try:
      self._bundle.Verify()
    except block_disk.InvalidRawDiskError:
      return
    self.fail()

  def testRootRawDiskVerifiesRootDestination(self):
    """Tests that destination directory must be /."""
    self._bundle.AddSource(self.tmp_path, arcname='/tmp')
    self._bundle.SetKey('key')
    try:
      self._bundle.Verify()
    except block_disk.InvalidRawDiskError:
      return
    self.fail()


def main():
  logging.basicConfig(level=logging.DEBUG)
  unittest.main()


if __name__ == '__main__':
  main()
