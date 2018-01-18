#!/usr/bin/python
# Copyright 2017 Google Inc. All Rights Reserved.
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

"""Unittest for compat.py module."""

import sys

import google_compute_engine.compat
from google_compute_engine.test_compat import mock
from google_compute_engine.test_compat import unittest
from google_compute_engine.test_compat import urlretrieve

try:
  # Import `reload` regardless of Python version.
  from importlib import reload
  from imp import reload
except:
  pass


class CompatTest(unittest.TestCase):

  @mock.patch('google_compute_engine.compat.subprocess.check_call')
  def testCurlRetrieve(self, mock_call):
    url = 'http://www.example.com/script.sh'
    filename = None
    expected = ['curl', '--max-time', mock.ANY, '--retry', mock.ANY, '--', url]

    if sys.version_info < (2, 7, 9):
      urlretrieve.urlretrieve(url, filename)
      mock_call.assert_called_with(expected)
    else:
      pass

  @mock.patch('google_compute_engine.compat.subprocess.check_call')
  def testCurlRetrieveFilename(self, mock_call):
    url = 'http://www.example.com/script.sh'
    filename = '/tmp/filename.txt'
    expected = [
        'curl', '--max-time', mock.ANY, '--retry', mock.ANY, '-o', filename,
        '--', url,
    ]

    if sys.version_info < (2, 7, 9):
      urlretrieve.urlretrieve(url, filename)
      mock_call.assert_called_with(expected)
    else:
      pass

  @mock.patch('google_compute_engine.compat.subprocess.check_call')
  @mock.patch('google_compute_engine.compat.urlretrieve.urlretrieve')
  def testUrlRetrieve(self, mock_retrieve, mock_call):
    url = 'http://www.example.com/script.sh'
    filename = '/tmp/filename.txt'
    args = ['arg1', 'arg2', 'arg3']
    kwargs = {'kwarg1': 1, 'kwarg2': 2}

    if sys.version_info >= (2, 7, 9):
      urlretrieve.urlretrieve(url, filename, *args, **kwargs)
      mock_retrieve.assert_called_once_with(url, filename, *args, **kwargs)
      mock_call.assert_not_called()
    else:
      pass

  def testGetDistroUtils_Debian8(self):
    self.verifyDistroUtils(
        ('debian', '8.10', ''),
        google_compute_engine.distro.debian_8.utils)

  def testGetDistroUtils_Debian9(self):
    self.verifyDistroUtils(
        ('debian', '9.3', ''),
        google_compute_engine.distro.debian_9.utils)

  def testGetDistroUtils_SUSE(self):
    self.verifyDistroUtils(
        ('SUSE Linux Enterprise Server ', '12', 'x86_64'),
        google_compute_engine.distro.debian_9.utils)

  def testGetDistroUtils_CentOS6(self):
    self.verifyDistroUtils(
        ('CentOS Linux', '6.4.3', 'Core'),
        google_compute_engine.distro.el_6.utils)

  def testGetDistroUtils_CentOS7(self):
    self.verifyDistroUtils(
        ('CentOS Linux', '7.4.1708', 'Core'),
        google_compute_engine.distro.el_7.utils)

  def testGetDistroUtils_CentOS8(self):
    self.verifyDistroUtils(
        ('CentOS Linux', '8.4.3', 'Core'),
        google_compute_engine.distro.debian_9.utils)

  def testGetDistroUtils_RHEL6(self):
    self.verifyDistroUtils(
        ('Red Hat Enterprise Linux Server', '6.3.2', ''),
        google_compute_engine.distro.el_6.utils)

  def testGetDistroUtils_RHEL7(self):
    self.verifyDistroUtils(
        ('Red Hat Enterprise Linux Server', '7.4', ''),
        google_compute_engine.distro.el_7.utils)

  def testGetDistroUtils_RHEL8(self):
    self.verifyDistroUtils(
        ('Red Hat Enterprise Linux Server', '8.5.1', ''),
        google_compute_engine.distro.debian_9.utils)

  def testGetDistroUtils_Empty(self):
    self.verifyDistroUtils(
        ('', '', ''),
        google_compute_engine.distro.debian_9.utils)

  def testGetDistroUtils_Unknown(self):
    self.verifyDistroUtils(
        ('xxxx', 'xxxx', 'xxxx'),
        google_compute_engine.distro.debian_9.utils)

  def verifyDistroUtils(self, actual, expected):
    with mock.patch(
        'google_compute_engine.compat.platform.linux_distribution',
        return_value=actual):
      reload(google_compute_engine.compat)
      self.assertEqual(expected, google_compute_engine.compat.distro_utils)


if __name__ == '__main__':
  unittest.main()
