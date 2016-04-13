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


class ImageBundleTest(unittest.TestCase):

  def testRunCommand(self):
    """Run a simple command and verify it works."""
    utils.RunCommand(['ls', '/'])

  def testRunCommandThatFails(self):
    """Run a command that will fail and verify it raises the correct error."""
    def RunCommandUnderTest():
      non_existent_path = '/' + uuid.uuid4().hex
      utils.RunCommand(['mkfs', '-t', 'ext4', non_existent_path])
    self.assertRaises(subprocess.CalledProcessError, RunCommandUnderTest)


def main():
  logging.basicConfig(level=logging.DEBUG)
  unittest.main()


if __name__ == '__main__':
  main()

