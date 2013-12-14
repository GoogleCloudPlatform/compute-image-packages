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

"""Unittest for utils.py module."""

__pychecker__ = 'no-local'  # for unittest

import logging
import subprocess
import unittest
import uuid

from gcimagebundlelib import utils

DF_T_TEST_OUTPUT = '''Filesystem     Type     1K-blocks    Used Available Use% Mounted on
/dev/sda1      ext4      94824284 5804652  84179800   7% /
none           tmpfs            4       0         4   0% /sys/fs/cgroup
udev           devtmpfs   4078660       4   4078656   1% /dev
tmpfs          tmpfs       817748     896    816852   1% /run
none           tmpfs         5120       0      5120   0% /run/lock
none           tmpfs      4088732     212   4088520   1% /run/shm
none           tmpfs       102400      52    102348   1% /run/user
'''


class ImageBundleTest(unittest.TestCase):

  def testRunCommand(self):
    """Run a simple command and verify it works."""
    utils.RunCommand(['ls', '/'])

  def testRunCommandThatFails(self):
    """Run a command that will fail and verify it raises the correct error."""
    non_existent_path = '/' + uuid.uuid4().hex
    with self.assertRaises(subprocess.CalledProcessError):
      utils.RunCommand(['mkfs', '-t', 'ext4', non_existent_path])

  def testTableToDict(self):
    fs_table = utils.TableToDict(DF_T_TEST_OUTPUT)
    self.assertEqual(7, len(fs_table))
    for item in fs_table:
      self.assertEqual(7, len(item.keys()))
      self.assertListEqual(item.keys(),
                           ['fileystem',
                            'type',
                            '1k-blocks',
                            'used',
                            'available',
                            'use%',
                            'mounted'])

def main():
  logging.basicConfig(level=logging.DEBUG)
  unittest.main()


if __name__ == '__main__':
  main()

