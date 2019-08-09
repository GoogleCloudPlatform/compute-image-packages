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
from google_compute_engine.test_compat import reload_import
from google_compute_engine.test_compat import unittest
from google_compute_engine.test_compat import urlretrieve


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

  @mock.patch('google_compute_engine.compat.distro.linux_distribution')
  def testDistroCompatLinux(self, mock_call):
    test_cases = {
        ('Fedora', '28', ''):
            google_compute_engine.distro_lib.el_7.utils,
        ('debian', '9.3', ''):
            google_compute_engine.distro_lib.debian_9.utils,
        ('debian', '10.3', ''):
            google_compute_engine.distro_lib.debian_9.utils,
        ('SUSE Linux Enterprise Server', '12', 'x86_64'):
            google_compute_engine.distro_lib.sles_12.utils,
        ('SUSE Linux Enterprise Server', '13', 'x86_64'):
            google_compute_engine.distro_lib.sles_12.utils,
        ('CentOS Linux', '6.4.3', 'Core'):
            google_compute_engine.distro_lib.el_6.utils,
        ('CentOS Linux', '7.4.1708', 'Core'):
            google_compute_engine.distro_lib.el_7.utils,
        ('CentOS Linux', '8.4.3', 'Core'):
            google_compute_engine.distro_lib.el_7.utils,
        ('Red Hat Enterprise Linux Server', '6.3.2', ''):
            google_compute_engine.distro_lib.el_6.utils,
        ('Red Hat Enterprise Linux Server', '7.4', ''):
            google_compute_engine.distro_lib.el_7.utils,
        ('Red Hat Enterprise Linux Server', '8.5.1', ''):
            google_compute_engine.distro_lib.el_7.utils,
        ('', '', ''):
            google_compute_engine.distro_lib.debian_9.utils,
        ('xxxx', 'xxxx', 'xxxx'):
            google_compute_engine.distro_lib.debian_9.utils,
    }

    for distro in test_cases:
      mock_call.return_value = distro
      reload_import(google_compute_engine.compat)
      self.assertEqual(
          test_cases[distro], google_compute_engine.compat.distro_utils)

  @mock.patch('google_compute_engine.compat.sys.platform', 'freebsd11')
  def testDistroCompatFreeBSD(self):
    reload_import(google_compute_engine.compat)
    self.assertEqual(
        google_compute_engine.distro_lib.freebsd_11.utils,
        google_compute_engine.compat.distro_utils)


if __name__ == '__main__':
  unittest.main()
