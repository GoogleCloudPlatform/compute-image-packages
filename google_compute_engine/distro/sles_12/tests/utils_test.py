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

from google_compute_engine.distro.sles_12 import utils
from google_compute_engine.test_compat import builtin
from google_compute_engine.test_compat import mock
from google_compute_engine.test_compat import unittest


class UtilsTest(unittest.TestCase):

  def setUp(self):
    self.mock_logger = mock.Mock()
    self.mock_setup = mock.create_autospec(utils.Utils)
    self.mock_setup.network_path = '/etc/sysconfig/network'

  def testEnableNetworkInterfacesWithSingleNic(self):
    mocks = mock.Mock()

    utils.Utils.EnableNetworkInterfaces(
        self.mock_setup, ['eth0'], self.mock_logger)
    expected_calls = []
    self.assertEqual(mocks.mock_calls, expected_calls)

  def testEnableNetworkInterfacesWithMultipleNics(self):
    mocks = mock.Mock()
    mocks.attach_mock(self.mock_setup._WriteIfcfg, 'writeIfcfg')
    mocks.attach_mock(self.mock_setup._Ifup, 'ifup')

    utils.Utils.EnableNetworkInterfaces(
        self.mock_setup, ['eth0', 'eth1', 'eth2'], self.mock_logger)
    expected_calls = [
        mock.call.writeIfcfg(['eth1', 'eth2'], mock.ANY),
        mock.call.ifup(['eth1', 'eth2'], mock.ANY),
    ]
    self.assertEqual(mocks.mock_calls, expected_calls)

  def testWriteIfcfg(self):
    mocks = mock.Mock()
    mock_open = mock.mock_open()
    mocks.attach_mock(mock_open, 'open')
    with mock.patch('%s.open' % builtin, mock_open, create=False):

      utils.Utils._WriteIfcfg(
          self.mock_setup, ['eth1', 'eth2'], self.mock_logger)
      expected_calls = [
          mock.call.open('/etc/sysconfig/network/ifcfg-eth1', 'w'),
          mock.call.open().__enter__(),
          mock.call.open().write(mock.ANY),
          mock.call.open().__exit__(None, None, None),
          mock.call.open('/etc/sysconfig/network/ifcfg-eth2', 'w'),
          mock.call.open().__enter__(),
          mock.call.open().write(mock.ANY),
          mock.call.open().__exit__(None, None, None),
      ]
      self.assertEqual(mocks.mock_calls, expected_calls)

  @mock.patch(
      'google_compute_engine.distro.sles_12.utils.subprocess.check_call')
  def testIfup(self, mock_call):
    mocks = mock.Mock()
    mocks.attach_mock(mock_call, 'call')
    mocks.attach_mock(self.mock_logger, 'logger')
    mock_call.side_effect = [
        None, subprocess.CalledProcessError(1, 'Test'),
    ]

    utils.Utils._Ifup(self.mock_setup, ['eth1', 'eth2'], self.mock_logger)
    utils.Utils._Ifup(self.mock_setup, ['eth1', 'eth2'], self.mock_logger)
    expectedIfupCall = [
        '/usr/sbin/wicked', 'ifup', '--timeout', '1', 'eth1', 'eth2',
    ]
    expected_calls = [
        mock.call.call(expectedIfupCall),
        mock.call.call(expectedIfupCall),
        mock.call.logger.warning(mock.ANY, ['eth1', 'eth2']),
    ]
    self.assertEqual(mocks.mock_calls, expected_calls)
