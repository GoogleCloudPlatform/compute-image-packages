#!/usr/bin/python
# Copyright 2018 Google Inc. All Rights Reserved.
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

"""Unittest for distro/utils.py module."""

import subprocess

from google_compute_engine.distro import helpers
from google_compute_engine.test_compat import mock
from google_compute_engine.test_compat import unittest


class HelpersTest(unittest.TestCase):

  def setUp(self):
    self.mock_logger = mock.Mock()

  @mock.patch('google_compute_engine.distro.helpers.os.path.exists')
  @mock.patch('google_compute_engine.distro.helpers.subprocess.check_call')
  def testCallDhClient(self, mock_call, mock_exists):
    mocks = mock.Mock()
    mocks.attach_mock(mock_exists, 'exists')
    mocks.attach_mock(mock_call, 'call')
    mocks.attach_mock(self.mock_logger, 'logger')

    mock_exists.side_effect = [False, True]
    mock_call.side_effect = [
        None, None, None, None, None, None,
        subprocess.CalledProcessError(1, 'Test')
    ]

    helpers.CallDhClient(['a', 'b'], self.mock_logger, 'test_script')
    helpers.CallDhClient(['c', 'd'], self.mock_logger, 'test_script')
    helpers.CallDhClient(['e', 'f'], self.mock_logger, None)
    helpers.CallDhClient(['g', 'h'], self.mock_logger, None)

    expected_calls = [
        mock.call.logger.info(mock.ANY, ['a', 'b']),
        mock.call.exists('test_script'),
        mock.call.call(['dhclient', '-x', 'a', 'b']),
        mock.call.call(['dhclient', 'a', 'b']),
        mock.call.logger.info(mock.ANY, ['c', 'd']),
        mock.call.exists('test_script'),
        mock.call.call(['dhclient', '-sf', 'test_script', '-x', 'c', 'd']),
        mock.call.call(['dhclient', '-sf', 'test_script', 'c', 'd']),
        mock.call.logger.info(mock.ANY, ['e', 'f']),
        mock.call.call(['dhclient', '-x', 'e', 'f']),
        mock.call.call(['dhclient', 'e', 'f']),
        mock.call.logger.info(mock.ANY, ['g', 'h']),
        mock.call.call(['dhclient', '-x', 'g', 'h']),
        mock.call.logger.warning(mock.ANY, ['g', 'h'])
    ]

    self.assertEqual(mocks.mock_calls, expected_calls)
