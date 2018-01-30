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

import os
import shutil
import tempfile

from google_compute_engine.distro.el_7 import utils
from google_compute_engine.test_compat import builtin
from google_compute_engine.test_compat import mock
from google_compute_engine.test_compat import unittest


class UtilsTest(unittest.TestCase):

  def setUp(self):
    # Create a temporary directory.
    self.test_dir = tempfile.mkdtemp()
    self.mock_logger = mock.Mock()
    self.mock_setup = mock.create_autospec(utils.Utils)
    self.mock_setup.network_path = '/etc/sysconfig/network-scripts'

  def tearDown(self):
    # Remove the directory after the test.
    shutil.rmtree(self.test_dir)

  def testModifyInterface(self):
    config_file = os.path.join(self.test_dir, 'config.cfg')
    config_content = [
        '# File comment.\n',
        'A="apple"\n',
        'B=banana\n',
        'B=banana\n',
    ]
    with open(config_file, 'w') as config:
      for line in config_content:
        config.write(line)

    # Write a value for an existing config without overriding it.
    utils.Utils._ModifyInterface(
        self.mock_setup, config_file, 'A', 'aardvark', replace=False)
    self.assertEquals(open(config_file).readlines(), config_content)
    # Write a value for a config that is not already set.
    utils.Utils._ModifyInterface(
        self.mock_setup, config_file, 'C', 'none', replace=False)
    config_content.append('C=none\n')
    self.assertEquals(open(config_file).readlines(), config_content)
    # Write a value for an existing config with replacement.
    utils.Utils._ModifyInterface(
        self.mock_setup, config_file, 'A', 'aardvark', replace=True)
    config_content[1] = 'A=aardvark\n'
    self.assertEquals(open(config_file).readlines(), config_content)
    # Write a value for an existing config with multiple occurrences.
    utils.Utils._ModifyInterface(
        self.mock_setup, config_file, 'B', '"banana"', replace=True)
    config_content[2] = config_content[3] = 'B="banana"\n'
    self.assertEquals(open(config_file).readlines(), config_content)

  @mock.patch('google_compute_engine.distro.el_7.utils.os.path.exists')
  def testDisableNetworkManager(self, mock_exists):
    mock_open = mock.mock_open()
    mocks = mock.Mock()
    mocks.attach_mock(mock_exists, 'exists')
    mocks.attach_mock(mock_open, 'open')
    mocks.attach_mock(self.mock_logger, 'logger')
    mocks.attach_mock(self.mock_setup._ModifyInterface, 'modify')
    mock_exists.side_effect = [True, False]

    with mock.patch('%s.open' % builtin, mock_open, create=False):
      utils.Utils._DisableNetworkManager(
          self.mock_setup, ['eth0', 'eth1'], self.mock_logger)
      expected_calls = [
          mock.call.exists('/etc/sysconfig/network-scripts/ifcfg-eth0'),
          mock.call.modify(mock.ANY, 'DEVICE', 'eth0', replace=False),
          mock.call.modify(mock.ANY, 'NM_CONTROLLED', 'no', replace=True),
          mock.call.exists('/etc/sysconfig/network-scripts/ifcfg-eth1'),
          mock.call.open('/etc/sysconfig/network-scripts/ifcfg-eth1', 'w'),
          mock.call.open().__enter__(),
          mock.call.open().write(mock.ANY),
          mock.call.open().__exit__(None, None, None),
          mock.call.logger.info(mock.ANY, 'eth1'),
      ]
      self.assertEqual(mocks.mock_calls, expected_calls)

  @mock.patch('google_compute_engine.distro.el_7.utils.os.path.exists')
  @mock.patch('google_compute_engine.distro.helpers.CallDhclient')
  def testEnableNetworkInterfaces(self, mock_call, mock_exists):
    mocks = mock.Mock()
    mocks.attach_mock(mock_exists, 'exists')
    mocks.attach_mock(self.mock_logger, 'logger')
    mocks.attach_mock(self.mock_setup._DisableNetworkManager, 'disable')
    mocks.attach_mock(mock_call, 'call_dhclient')
    mock_exists.side_effect = [True, False]

    # Enable interfaces with network manager enabled.
    utils.Utils.EnableNetworkInterfaces(
        self.mock_setup, ['A', 'B'], self.mock_logger)
    # Enable interfaces with network manager is not present.
    utils.Utils.EnableNetworkInterfaces(
        self.mock_setup, ['C', 'D'], self.mock_logger)
    expected_calls = [
        mock.call.exists('/etc/sysconfig/network-scripts'),
        mock.call.disable(['A', 'B'], mock.ANY),
        mock.call.call_dhclient(['A', 'B'], mock.ANY),
        mock.call.exists('/etc/sysconfig/network-scripts'),
        mock.call.call_dhclient(['C', 'D'], mock.ANY),
    ]
    self.assertEqual(mocks.mock_calls, expected_calls)
