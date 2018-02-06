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

"""Unittest for ip_forwarding_daemon.py module."""

from google_compute_engine.network.ip_forwarding import ip_forwarding_daemon
from google_compute_engine.test_compat import mock
from google_compute_engine.test_compat import unittest


class IpForwardingDaemonTest(unittest.TestCase):

  def setUp(self):
    self.mock_logger = mock.Mock()
    self.mock_watcher = mock.Mock()
    self.mock_ip_forwarding_utils = mock.Mock()
    self.mock_network_utils = mock.Mock()

    self.mock_setup = mock.create_autospec(
        ip_forwarding_daemon.IpForwardingDaemon)
    self.mock_setup.logger = self.mock_logger
    self.mock_setup.watcher = self.mock_watcher
    self.mock_setup.ip_forwarding_utils = self.mock_ip_forwarding_utils
    self.mock_setup.network_utils = self.mock_network_utils

  @mock.patch('google_compute_engine.network.ip_forwarding.ip_forwarding_daemon.ip_forwarding_utils')
  @mock.patch('google_compute_engine.network.ip_forwarding.ip_forwarding_daemon.network_utils')
  @mock.patch('google_compute_engine.network.ip_forwarding.ip_forwarding_daemon.metadata_watcher')
  @mock.patch('google_compute_engine.network.ip_forwarding.ip_forwarding_daemon.logger')
  @mock.patch('google_compute_engine.network.ip_forwarding.ip_forwarding_daemon.file_utils')
  def testIpForwardingDaemon(
      self, mock_lock, mock_logger, mock_watcher, mock_network_utils,
      mock_ip_forwarding_utils):
    mock_logger_instance = mock.Mock()
    mock_logger.Logger.return_value = mock_logger_instance
    mocks = mock.Mock()
    mocks.attach_mock(mock_lock, 'lock')
    mocks.attach_mock(mock_logger, 'logger')
    mocks.attach_mock(mock_network_utils, 'network')
    mocks.attach_mock(mock_ip_forwarding_utils, 'forwarding')
    mocks.attach_mock(mock_watcher, 'watcher')
    metadata_key = ip_forwarding_daemon.IpForwardingDaemon.network_interfaces
    with mock.patch.object(
        ip_forwarding_daemon.IpForwardingDaemon,
        'HandleNetworkInterfaces') as mock_handle:
      ip_forwarding_daemon.IpForwardingDaemon(proto_id='66', debug=True)
      expected_calls = [
          mock.call.logger.Logger(name=mock.ANY, debug=True, facility=mock.ANY),
          mock.call.watcher.MetadataWatcher(logger=mock_logger_instance),
          mock.call.network.NetworkUtils(logger=mock_logger_instance),
          mock.call.forwarding.IpForwardingUtils(
              logger=mock_logger_instance, proto_id='66'),
          mock.call.lock.LockFile(ip_forwarding_daemon.LOCKFILE),
          mock.call.lock.LockFile().__enter__(),
          mock.call.logger.Logger().info(mock.ANY),
          mock.call.watcher.MetadataWatcher().WatchMetadata(
              mock_handle, metadata_key=metadata_key, recursive=True,
              timeout=mock.ANY),
          mock.call.lock.LockFile().__exit__(None, None, None),
      ]
      self.assertEqual(mocks.mock_calls, expected_calls)

  @mock.patch('google_compute_engine.network.ip_forwarding.ip_forwarding_daemon.ip_forwarding_utils')
  @mock.patch('google_compute_engine.network.ip_forwarding.ip_forwarding_daemon.network_utils')
  @mock.patch('google_compute_engine.network.ip_forwarding.ip_forwarding_daemon.metadata_watcher')
  @mock.patch('google_compute_engine.network.ip_forwarding.ip_forwarding_daemon.logger')
  @mock.patch('google_compute_engine.network.ip_forwarding.ip_forwarding_daemon.file_utils')
  def testIpForwardingDaemonError(
      self, mock_lock, mock_logger, mock_watcher, mock_network_utils,
      mock_ip_forwarding_utils):
    mock_logger_instance = mock.Mock()
    mock_logger.Logger.return_value = mock_logger_instance
    mocks = mock.Mock()
    mocks.attach_mock(mock_lock, 'lock')
    mocks.attach_mock(mock_logger, 'logger')
    mocks.attach_mock(mock_network_utils, 'network')
    mocks.attach_mock(mock_ip_forwarding_utils, 'forwarding')
    mocks.attach_mock(mock_watcher, 'watcher')
    mock_lock.LockFile.side_effect = IOError('Test Error')
    with mock.patch.object(
        ip_forwarding_daemon.IpForwardingDaemon, 'HandleNetworkInterfaces'):
      ip_forwarding_daemon.IpForwardingDaemon()
      expected_calls = [
          mock.call.logger.Logger(
              name=mock.ANY, debug=False, facility=mock.ANY),
          mock.call.watcher.MetadataWatcher(logger=mock_logger_instance),
          mock.call.network.NetworkUtils(logger=mock_logger_instance),
          mock.call.forwarding.IpForwardingUtils(
              logger=mock_logger_instance, proto_id=None),
          mock.call.lock.LockFile(ip_forwarding_daemon.LOCKFILE),
          mock.call.logger.Logger().warning('Test Error'),
      ]
      self.assertEqual(mocks.mock_calls, expected_calls)

  def testLogForwardedIpChanges(self):
    ip_forwarding_daemon.IpForwardingDaemon._LogForwardedIpChanges(
        self.mock_setup, [], [], [], [], '1')
    ip_forwarding_daemon.IpForwardingDaemon._LogForwardedIpChanges(
        self.mock_setup, ['a'], ['a'], [], [], '2')
    ip_forwarding_daemon.IpForwardingDaemon._LogForwardedIpChanges(
        self.mock_setup, ['a'], [], [], ['a'], '3')
    ip_forwarding_daemon.IpForwardingDaemon._LogForwardedIpChanges(
        self.mock_setup, ['a', 'b'], ['b'], [], ['a'], '4')
    ip_forwarding_daemon.IpForwardingDaemon._LogForwardedIpChanges(
        self.mock_setup, ['a'], ['b'], ['b'], ['a'], '5')
    expected_calls = [
        mock.call.info(mock.ANY, '3', ['a'], None, None, ['a']),
        mock.call.info(mock.ANY, '4', ['a', 'b'], ['b'], None, ['a']),
        mock.call.info(mock.ANY, '5', ['a'], ['b'], ['b'], ['a']),
    ]
    self.assertEqual(self.mock_logger.mock_calls, expected_calls)

  def testAddForwardedIp(self):
    ip_forwarding_daemon.IpForwardingDaemon._AddForwardedIps(
        self.mock_setup, [], 'interface')
    self.assertEqual(self.mock_ip_forwarding_utils.mock_calls, [])

    ip_forwarding_daemon.IpForwardingDaemon._AddForwardedIps(
        self.mock_setup, ['a', 'b', 'c'], 'interface')
    expected_calls = [
        mock.call.AddForwardedIp('a', 'interface'),
        mock.call.AddForwardedIp('b', 'interface'),
        mock.call.AddForwardedIp('c', 'interface'),
    ]
    self.assertEqual(self.mock_ip_forwarding_utils.mock_calls, expected_calls)

  def testRemoveForwardedIp(self):
    ip_forwarding_daemon.IpForwardingDaemon._RemoveForwardedIps(
        self.mock_setup, [], 'interface')
    self.assertEqual(self.mock_ip_forwarding_utils.mock_calls, [])

    ip_forwarding_daemon.IpForwardingDaemon._RemoveForwardedIps(
        self.mock_setup, ['a', 'b', 'c'], 'interface')
    expected_calls = [
        mock.call.RemoveForwardedIp('a', 'interface'),
        mock.call.RemoveForwardedIp('b', 'interface'),
        mock.call.RemoveForwardedIp('c', 'interface'),
    ]
    self.assertEqual(self.mock_ip_forwarding_utils.mock_calls, expected_calls)

  def testHandleForwardedIps(self):
    configured = ['c', 'c', 'b', 'b', 'a', 'a']
    desired = ['d', 'd', 'c']
    mocks = mock.Mock()
    mocks.attach_mock(self.mock_ip_forwarding_utils, 'forwarding')
    mocks.attach_mock(self.mock_setup, 'setup')
    self.mock_ip_forwarding_utils.ParseForwardedIps.return_value = desired
    self.mock_ip_forwarding_utils.GetForwardedIps.return_value = configured
    forwarded_ips = 'forwarded ips'
    interface = 'interface'
    expected_add = ['d']
    expected_remove = ['a', 'b']

    ip_forwarding_daemon.IpForwardingDaemon._HandleForwardedIps(
        self.mock_setup, forwarded_ips, interface)
    expected_calls = [
        mock.call.forwarding.ParseForwardedIps(forwarded_ips),
        mock.call.forwarding.GetForwardedIps(interface),
        mock.call.setup._LogForwardedIpChanges(
            configured, desired, expected_add, expected_remove, interface),
        mock.call.setup._AddForwardedIps(expected_add, interface),
        mock.call.setup._RemoveForwardedIps(expected_remove, interface),
    ]
    self.assertEqual(mocks.mock_calls, expected_calls)

  def testHandleNetworkInterfaces(self):
    self.mock_setup.ip_aliases = False
    self.mock_setup.target_instance_ips = False
    mocks = mock.Mock()
    mocks.attach_mock(self.mock_network_utils, 'network')
    mocks.attach_mock(self.mock_setup, 'setup')
    self.mock_network_utils.GetNetworkInterface.side_effect = [
        'eth0', 'eth1', 'eth2', 'eth3', None]
    result = [
        {
            'mac': '1',
            'forwardedIps': ['a']
        },
        {
            'mac': '2',
            'forwardedIps': ['b'],
            'ipAliases': ['banana'],
            'targetInstanceIps': ['baklava'],
        },
        {
            'mac': '3',
            'ipAliases': ['cherry'],
            'targetInstanceIps': ['cake'],
        },
        {
            'mac': '4'
        },
        {
            'forwardedIps': ['d'],
            'ipAliases': ['date'],
            'targetInstanceIps': ['doughnuts'],
        },
    ]

    ip_forwarding_daemon.IpForwardingDaemon.HandleNetworkInterfaces(
        self.mock_setup, result)
    expected_calls = [
        mock.call.network.GetNetworkInterface('1'),
        mock.call.setup._HandleForwardedIps(['a'], 'eth0'),
        mock.call.network.GetNetworkInterface('2'),
        mock.call.setup._HandleForwardedIps(['b'], 'eth1'),
        mock.call.network.GetNetworkInterface('3'),
        mock.call.setup._HandleForwardedIps([], 'eth2'),
        mock.call.network.GetNetworkInterface('4'),
        mock.call.setup._HandleForwardedIps([], 'eth3'),
        mock.call.network.GetNetworkInterface(None),
        mock.call.setup.logger.warning(mock.ANY, None),
    ]
    self.assertEqual(mocks.mock_calls, expected_calls)

  def testHandleNetworkInterfacesFeatures(self):
    self.mock_setup.ip_aliases = True
    self.mock_setup.target_instance_ips = True
    mocks = mock.Mock()
    mocks.attach_mock(self.mock_network_utils, 'network')
    mocks.attach_mock(self.mock_setup, 'setup')
    self.mock_network_utils.GetNetworkInterface.side_effect = [
        'eth0', 'eth1', 'eth2', 'eth3', None]
    result = [
        {
            'mac': '1',
            'forwardedIps': ['a']
        },
        {
            'mac': '2',
            'forwardedIps': ['b'],
            'ipAliases': ['banana'],
            'targetInstanceIps': ['baklava'],
        },
        {
            'mac': '3',
            'ipAliases': ['cherry'],
            'targetInstanceIps': ['cake'],
        },
        {
            'mac': '4'
        },
        {
            'forwardedIps': ['d'],
            'ipAliases': ['date'],
            'targetInstanceIps': ['doughnuts'],
        },
    ]

    ip_forwarding_daemon.IpForwardingDaemon.HandleNetworkInterfaces(
        self.mock_setup, result)
    expected_calls = [
        mock.call.network.GetNetworkInterface('1'),
        mock.call.setup._HandleForwardedIps(['a'], 'eth0'),
        mock.call.network.GetNetworkInterface('2'),
        mock.call.setup._HandleForwardedIps(['b', 'banana', 'baklava'], 'eth1'),
        mock.call.network.GetNetworkInterface('3'),
        mock.call.setup._HandleForwardedIps(['cherry', 'cake'], 'eth2'),
        mock.call.network.GetNetworkInterface('4'),
        mock.call.setup._HandleForwardedIps([], 'eth3'),
        mock.call.network.GetNetworkInterface(None),
        mock.call.setup.logger.warning(mock.ANY, None),
    ]
    self.assertEqual(mocks.mock_calls, expected_calls)


if __name__ == '__main__':
  unittest.main()
