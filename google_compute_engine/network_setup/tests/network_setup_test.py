#!/usr/bin/python
# Copyright 2016 Google Inc. All Rights Reserved.
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

"""Unittest for network_setup.py module."""

import os
import shutil
import subprocess
import tempfile

from google_compute_engine.network_setup import network_setup
from google_compute_engine.test_compat import builtin
from google_compute_engine.test_compat import mock
from google_compute_engine.test_compat import unittest


class NetworkSetupTest(unittest.TestCase):

  def setUp(self):
    # Create a temporary directory.
    self.test_dir = tempfile.mkdtemp()

    self.mock_logger = mock.Mock()
    self.mock_watcher = mock.Mock()
    self.mock_ip_forwarding_utils = mock.Mock()
    self.mock_network_utils = mock.Mock()
    self.metadata_key = 'metadata_key'

    self.mock_setup = mock.create_autospec(network_setup.NetworkSetup)
    self.mock_setup.logger = self.mock_logger
    self.mock_setup.watcher = self.mock_watcher
    self.mock_setup.network_utils = self.mock_network_utils
    self.mock_setup.network_interfaces = self.metadata_key
    self.mock_setup.dhclient_script = '/bin/script'
    self.mock_setup.dhcp_command = ''

  def tearDown(self):
    # Remove the directory after the test.
    shutil.rmtree(self.test_dir)

  @mock.patch('google_compute_engine.network_setup.network_setup.network_utils')
  @mock.patch('google_compute_engine.network_setup.network_setup.metadata_watcher')
  @mock.patch('google_compute_engine.network_setup.network_setup.logger')
  def testNetworkSetup(self, mock_logger, mock_watcher, mock_network_utils):
    mock_logger_instance = mock.Mock()
    mock_logger.Logger.return_value = mock_logger_instance
    mocks = mock.Mock()
    mocks.attach_mock(mock_logger, 'logger')
    mocks.attach_mock(mock_watcher, 'watcher')
    mocks.attach_mock(mock_network_utils, 'network')
    with mock.patch.object(
        network_setup.NetworkSetup, '_SetupNetworkInterfaces'):
      network_setup.NetworkSetup(debug=True)
      expected_calls = [
          mock.call.logger.Logger(name=mock.ANY, debug=True, facility=mock.ANY),
          mock.call.watcher.MetadataWatcher(logger=mock_logger_instance),
          mock.call.network.NetworkUtils(logger=mock_logger_instance),
      ]
      self.assertEqual(mocks.mock_calls, expected_calls)

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
    network_setup.NetworkSetup._ModifyInterface(
        self.mock_setup, config_file, 'A', 'aardvark', replace=False)
    self.assertEquals(open(config_file).readlines(), config_content)
    # Write a value for a config that is not already set.
    network_setup.NetworkSetup._ModifyInterface(
        self.mock_setup, config_file, 'C', 'none', replace=False)
    config_content.append('C=none\n')
    self.assertEquals(open(config_file).readlines(), config_content)
    # Write a value for an existing config with replacement.
    network_setup.NetworkSetup._ModifyInterface(
        self.mock_setup, config_file, 'A', 'aardvark', replace=True)
    config_content[1] = 'A=aardvark\n'
    self.assertEquals(open(config_file).readlines(), config_content)
    # Write a value for an existing config with multiple occurrences.
    network_setup.NetworkSetup._ModifyInterface(
        self.mock_setup, config_file, 'B', '"banana"', replace=True)
    config_content[2] = config_content[3] = 'B="banana"\n'
    self.assertEquals(open(config_file).readlines(), config_content)

  @mock.patch('google_compute_engine.network_setup.network_setup.os.path.exists')
  def testDisableNetworkManager(self, mock_exists):
    mock_open = mock.mock_open()
    mocks = mock.Mock()
    mocks.attach_mock(mock_exists, 'exists')
    mocks.attach_mock(mock_open, 'open')
    mocks.attach_mock(self.mock_logger, 'logger')
    mocks.attach_mock(self.mock_setup._ModifyInterface, 'modify')
    mock_exists.side_effect = [True, False]

    with mock.patch('%s.open' % builtin, mock_open, create=False):
      network_setup.NetworkSetup._DisableNetworkManager(
          self.mock_setup, ['eth0', 'eth1'])
      expected_calls = [
          mock.call.exists('/etc/sysconfig/network-scripts/ifcfg-eth0'),
          mock.call.modify(mock.ANY, 'DEVICE', 'eth0', replace=False),
          mock.call.modify(mock.ANY, 'IPV6INIT', 'no', replace=True),
          mock.call.modify(mock.ANY, 'NM_CONTROLLED', 'no', replace=True),
          mock.call.exists('/etc/sysconfig/network-scripts/ifcfg-eth1'),
          mock.call.open('/etc/sysconfig/network-scripts/ifcfg-eth1', 'w'),
          mock.call.open().__enter__(),
          mock.call.open().write(mock.ANY),
          mock.call.open().__exit__(None, None, None),
          mock.call.logger.info(mock.ANY, 'eth1'),
      ]
      self.assertEqual(mocks.mock_calls, expected_calls)

  @mock.patch('google_compute_engine.network_setup.network_setup.subprocess.check_call')
  @mock.patch('google_compute_engine.network_setup.network_setup.os.path.exists')
  def testConfigureNetwork(self, mock_exists, mock_call):
    mocks = mock.Mock()
    mocks.attach_mock(mock_exists, 'exists')
    mocks.attach_mock(mock_call, 'call')
    mocks.attach_mock(self.mock_logger, 'logger')
    mock_exists.side_effect = [True, False, False]
    mock_call.side_effect = [
        None, None, None, None, subprocess.CalledProcessError(1, 'Test')]

    network_setup.NetworkSetup._ConfigureNetwork(self.mock_setup, ['a', 'b'])
    network_setup.NetworkSetup._ConfigureNetwork(self.mock_setup, ['c'])
    network_setup.NetworkSetup._ConfigureNetwork(self.mock_setup, [])
    expected_calls = [
        # Successfully configure the network using a managed dhclient script.
        mock.call.logger.info(mock.ANY, ['a', 'b']),
        mock.call.exists('/bin/script'),
        mock.call.call(['dhclient', '-sf', '/bin/script', '-x', 'a', 'b']),
        mock.call.call(['dhclient', '-sf', '/bin/script', 'a', 'b']),
        # Successfully configure the network using the default dhclient script.
        mock.call.logger.info(mock.ANY, ['c']),
        mock.call.exists('/bin/script'),
        mock.call.call(['dhclient', '-x', 'c']),
        mock.call.call(['dhclient', 'c']),
        # Exception while enabling the network interface.
        mock.call.logger.info(mock.ANY, []),
        mock.call.exists('/bin/script'),
        mock.call.call(['dhclient', '-x']),
        mock.call.logger.warning(mock.ANY, []),
    ]
    self.assertEqual(mocks.mock_calls, expected_calls)

  @mock.patch('google_compute_engine.network_setup.network_setup.subprocess.check_call')
  @mock.patch('google_compute_engine.network_setup.network_setup.os.path.exists')
  def testEnableNetworkInterfaces(self, mock_exists, mock_call):
    mocks = mock.Mock()
    mocks.attach_mock(mock_exists, 'exists')
    mocks.attach_mock(mock_call, 'call')
    mocks.attach_mock(self.mock_logger, 'logger')
    mocks.attach_mock(self.mock_setup._DisableNetworkManager, 'disable')
    mocks.attach_mock(self.mock_setup._ConfigureNetwork, 'configure')
    mock_exists.side_effect = [True, False]
    mock_call.side_effect = [None, subprocess.CalledProcessError(1, 'Test')]

    # Return immediately with fewer than two interfaces.
    network_setup.NetworkSetup._EnableNetworkInterfaces(self.mock_setup, None)
    network_setup.NetworkSetup._EnableNetworkInterfaces(self.mock_setup, [])
    # Enable interfaces with network manager enabled.
    network_setup.NetworkSetup._EnableNetworkInterfaces(
        self.mock_setup, ['A', 'B'])
    # Enable interfaces with network manager is not present.
    network_setup.NetworkSetup._EnableNetworkInterfaces(
        self.mock_setup, ['C', 'D'])
    # Run a user supplied command successfully.
    self.mock_setup.dhcp_command = 'success'
    network_setup.NetworkSetup._EnableNetworkInterfaces(
        self.mock_setup, ['E', 'F'])
    # Run a user supplied command and logger error messages.
    self.mock_setup.dhcp_command = 'failure'
    network_setup.NetworkSetup._EnableNetworkInterfaces(
        self.mock_setup, ['G', 'H'])

    expected_calls = [
        mock.call.exists('/etc/sysconfig/network-scripts'),
        mock.call.disable(['A', 'B']),
        mock.call.configure(['A', 'B']),
        mock.call.exists('/etc/sysconfig/network-scripts'),
        mock.call.configure(['C', 'D']),
        mock.call.call(['success']),
        mock.call.call(['failure']),
        mock.call.logger.warning(mock.ANY),
    ]
    self.assertEqual(mocks.mock_calls, expected_calls)

  def testSetupNetworkInterfaces(self):
    mocks = mock.Mock()
    mocks.attach_mock(self.mock_logger, 'logger')
    mocks.attach_mock(self.mock_watcher, 'watcher')
    mocks.attach_mock(self.mock_network_utils, 'network')
    mocks.attach_mock(self.mock_setup, 'setup')
    self.mock_watcher.GetMetadata.return_value = [
        {'mac': '1'}, {'mac': '2'}, {'mac': '3'}, {}]
    self.mock_network_utils.GetNetworkInterface.side_effect = [
        'eth0', 'eth1', None, None]

    with mock.patch.object(
        network_setup.NetworkSetup, '_EnableNetworkInterfaces'):
      self.mock_setup.dhcp_command = 'command'
      network_setup.NetworkSetup._SetupNetworkInterfaces(self.mock_setup)
      expected_calls = [
          mock.call.watcher.GetMetadata(
              metadata_key=self.metadata_key, recursive=True),
          mock.call.network.GetNetworkInterface('1'),
          mock.call.network.GetNetworkInterface('2'),
          mock.call.network.GetNetworkInterface('3'),
          mock.call.logger.warning(mock.ANY, '3'),
          mock.call.network.GetNetworkInterface(None),
          mock.call.logger.warning(mock.ANY, None),
          mock.call.setup._EnableNetworkInterfaces(['eth0', 'eth1']),
      ]
      self.assertEqual(mocks.mock_calls, expected_calls)
