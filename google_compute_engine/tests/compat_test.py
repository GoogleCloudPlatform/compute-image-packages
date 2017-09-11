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

"""Unittest for logger.py module."""

import sys

from google_compute_engine.test_compat import mock
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


if __name__ == '__main__':
  unittest.main()
