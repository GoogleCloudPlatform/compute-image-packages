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

import subprocess

from google_compute_engine.network_setup import network_setup
from google_compute_engine.test_compat import mock
from google_compute_engine.test_compat import unittest


class NetworkSetupTest(unittest.TestCase):

  def setUp(self):
    self.mock_logger = mock.Mock()
    self.mock_watcher = mock.Mock()
    self.mock_ip_forwarding_utils = mock.Mock()
    self.mock_network_utils = mock.Mock()
    self.metadata_key = 'metadata_key'
    self.dhcp_binary = 'binary'

    self.mock_setup = mock.create_autospec(network_setup.NetworkSetup)
    self.mock_setup.logger = self.mock_logger
    self.mock_setup.watcher = self.mock_watcher
    self.mock_setup.network_utils = self.mock_network_utils
    self.mock_setup.network_interfaces = self.metadata_key
    self.mock_setup.dhcp_binary = self.dhcp_binary

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
      network_setup.NetworkSetup(dhcp_binary='binary', debug=True)
      expected_calls = [
          mock.call.logger.Logger(name=mock.ANY, debug=True, facility=mock.ANY),
          mock.call.watcher.MetadataWatcher(logger=mock_logger_instance),
          mock.call.network.NetworkUtils(logger=mock_logger_instance),
      ]
      self.assertEqual(mocks.mock_calls, expected_calls)

  @mock.patch('google_compute_engine.network_setup.network_setup.subprocess.check_call')
  def testEnableNetworkInterface(self, mock_call):
    mocks = mock.Mock()
    mocks.attach_mock(mock_call, 'call')
    mocks.attach_mock(self.mock_logger, 'logger')
    mocks.attach_mock(self.mock_watcher, 'watcher')
    mocks.attach_mock(self.mock_network_utils, 'network')
    mock_call.side_effect = [None, subprocess.CalledProcessError(1, 'Test')]
    self.mock_network_utils.IsEnabled.side_effect = [True, False, False]

    network_setup.NetworkSetup._EnableNetworkInterface(self.mock_setup, 'a')
    network_setup.NetworkSetup._EnableNetworkInterface(self.mock_setup, 'b')
    network_setup.NetworkSetup._EnableNetworkInterface(self.mock_setup, 'c')
    expected_calls = [
        # The network interface is already enabled.
        mock.call.network.IsEnabled('a'),
        # Successfully enable the network interface.
        mock.call.network.IsEnabled('b'),
        mock.call.logger.info(mock.ANY, 'b'),
        mock.call.call([self.dhcp_binary, 'b']),
        # Exception while enabling the network interface.
        mock.call.network.IsEnabled('c'),
        mock.call.logger.info(mock.ANY, 'c'),
        mock.call.call([self.dhcp_binary, 'c']),
        mock.call.logger.warning(mock.ANY, 'c'),
    ]
    self.assertEqual(mocks.mock_calls, expected_calls)

  def testSetupNetworkInterfaces(self):
    mocks = mock.Mock()
    mocks.attach_mock(self.mock_logger, 'logger')
    mocks.attach_mock(self.mock_watcher, 'watcher')
    mocks.attach_mock(self.mock_network_utils, 'network')
    mocks.attach_mock(self.mock_setup, 'setup')
    self.mock_watcher.GetMetadata.return_value = [
        {'mac': '1'}, {'mac': '2'}, {}]
    self.mock_network_utils.GetNetworkInterface.side_effect = [
        'eth0', None, None]

    with mock.patch.object(
        network_setup.NetworkSetup, '_EnableNetworkInterface'):
      network_setup.NetworkSetup._SetupNetworkInterfaces(self.mock_setup)
      expected_calls = [
          mock.call.watcher.GetMetadata(
              metadata_key=self.metadata_key, recursive=True),
          mock.call.network.GetNetworkInterface('1'),
          mock.call.setup._EnableNetworkInterface('eth0'),
          mock.call.network.GetNetworkInterface('2'),
          mock.call.logger.warning(mock.ANY, '2'),
          mock.call.network.GetNetworkInterface(None),
          mock.call.logger.warning(mock.ANY, None),
      ]
      self.assertEqual(mocks.mock_calls, expected_calls)
