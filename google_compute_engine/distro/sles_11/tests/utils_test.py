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
"""Unittest for utils.py module."""

import subprocess

from google_compute_engine.distro.sles_11 import utils
from google_compute_engine.test_compat import mock
from google_compute_engine.test_compat import unittest


class UtilsTest(unittest.TestCase):

  def setUp(self):
    self.mock_logger = mock.Mock()
    self.mock_setup = mock.create_autospec(utils.Utils)

  def testEnableNetworkInterfacesWithSingleNic(self):
    mocks = mock.Mock()

    utils.Utils.EnableNetworkInterfaces(
        self.mock_setup, ['eth0'], self.mock_logger)
    expected_calls = []
    self.assertEqual(mocks.mock_calls, expected_calls)

  def testEnableNetworkInterfacesWithMultipleNics(self):
    mocks = mock.Mock()
    mocks.attach_mock(self.mock_setup._Dhcpcd, 'dhcpcd')

    utils.Utils.EnableNetworkInterfaces(
        self.mock_setup, ['eth0', 'eth1', 'eth2'], self.mock_logger)
    expected_calls = [
        mock.call.dhcpcd(['eth1', 'eth2'], mock.ANY),
    ]
    self.assertEqual(mocks.mock_calls, expected_calls)

  @mock.patch(
      'google_compute_engine.distro.sles_11.utils.subprocess.check_call')
  def testDhcpcd(self, mock_call):
    mocks = mock.Mock()
    mocks.attach_mock(mock_call, 'call')
    mocks.attach_mock(self.mock_logger, 'logger')
    mock_call.side_effect = [
        None, None, None, None,
        subprocess.CalledProcessError(1, 'Test'),
        subprocess.CalledProcessError(1, 'Test'),
    ]

    utils.Utils._Dhcpcd(
        self.mock_setup, ['eth1', 'eth2', 'eth3'], self.mock_logger)
    expected_calls = [
        mock.call.call(['/sbin/dhcpcd', '-x', 'eth1']),
        mock.call.call(['/sbin/dhcpcd', 'eth1']),
        mock.call.call(['/sbin/dhcpcd', '-x', 'eth2']),
        mock.call.call(['/sbin/dhcpcd', 'eth2']),
        mock.call.call(['/sbin/dhcpcd', '-x', 'eth3']),
        mock.call.logger.info(mock.ANY, 'eth3'),
        mock.call.call(['/sbin/dhcpcd','eth3']),
        mock.call.logger.warning(mock.ANY, 'eth3'),
    ]
    self.assertEqual(mocks.mock_calls, expected_calls)
