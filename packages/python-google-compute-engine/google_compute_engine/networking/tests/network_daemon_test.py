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

"""Unittest for network_daemon.py module."""

from google_compute_engine import network_utils
from google_compute_engine.networking import network_daemon
from google_compute_engine.test_compat import mock
from google_compute_engine.test_compat import unittest


class NetworkDaemonTest(unittest.TestCase):

  def setUp(self):
    self.mock_logger = mock.Mock()
    self.mock_watcher = mock.Mock()
    self.mock_setup = mock.create_autospec(network_daemon.NetworkDaemon)
    self.mock_setup.logger = self.mock_logger
    self.mock_setup.watcher = self.mock_watcher
    self.mock_ip_forwarding = mock.Mock()
    self.mock_network_setup = mock.Mock()
    self.mock_network_utils = mock.Mock()
    self.mock_setup.ip_forwarding = self.mock_ip_forwarding
    self.mock_setup.network_setup = self.mock_network_setup
    self.mock_setup.network_utils = self.mock_network_utils

  @mock.patch('google_compute_engine.networking.network_daemon.ip_forwarding')
  @mock.patch('google_compute_engine.networking.network_daemon.network_setup')
  @mock.patch('google_compute_engine.networking.network_daemon.network_utils')
  @mock.patch('google_compute_engine.networking.network_daemon.metadata_watcher')
  @mock.patch('google_compute_engine.networking.network_daemon.logger')
  @mock.patch('google_compute_engine.networking.network_daemon.file_utils')
  def testNetworkDaemon(
      self, mock_lock, mock_logger, mock_watcher, mock_network_utils,
      mock_network_setup, mock_ip_forwarding):
    mock_logger_instance = mock.Mock()
    mock_logger.Logger.return_value = mock_logger_instance
    mocks = mock.Mock()
    mocks.attach_mock(mock_lock, 'lock')
    mocks.attach_mock(mock_logger, 'logger')
    mocks.attach_mock(mock_network_utils, 'network')
    mocks.attach_mock(mock_ip_forwarding, 'forwarding')
    mocks.attach_mock(mock_network_setup, 'network_setup')
    mocks.attach_mock(mock_watcher, 'watcher')

    with mock.patch.object(
        network_daemon.NetworkDaemon, 'HandleNetworkInterfaces'
    ) as mock_handle:
      network_daemon.NetworkDaemon(
          ip_forwarding_enabled=True,
          proto_id='66',
          ip_aliases=None,
          target_instance_ips=None,
          dhclient_script='x',
          dhcp_command='y',
          network_setup_enabled=True,
          debug=True)
      expected_calls = [
          mock.call.logger.Logger(name=mock.ANY, debug=True, facility=mock.ANY),
          mock.call.forwarding.IpForwarding(proto_id='66', debug=True),
          mock.call.network_setup.NetworkSetup(
              debug=True, dhclient_script='x', dhcp_command='y'),
          mock.call.network.NetworkUtils(logger=mock_logger_instance),
          mock.call.watcher.MetadataWatcher(logger=mock_logger_instance),
          mock.call.lock.LockFile(network_daemon.LOCKFILE),
          mock.call.lock.LockFile().__enter__(),
          mock.call.logger.Logger().info(mock.ANY),
          mock.call.watcher.MetadataWatcher().WatchMetadata(
              mock_handle, metadata_key="instance/", recursive=True,
              timeout=mock.ANY),
          mock.call.lock.LockFile().__exit__(None, None, None),
      ]
      self.assertEqual(mocks.mock_calls, expected_calls)

  @mock.patch('google_compute_engine.networking.network_daemon.ip_forwarding')
  @mock.patch('google_compute_engine.networking.network_daemon.network_setup')
  @mock.patch('google_compute_engine.networking.network_daemon.network_utils')
  @mock.patch('google_compute_engine.networking.network_daemon.metadata_watcher')
  @mock.patch('google_compute_engine.networking.network_daemon.logger')
  @mock.patch('google_compute_engine.networking.network_daemon.file_utils')
  def testNetworkDaemonError(
      self, mock_lock, mock_logger, mock_watcher, mock_network_utils,
      mock_network_setup, mock_ip_forwarding):
    mock_logger_instance = mock.Mock()
    mock_logger.Logger.return_value = mock_logger_instance
    mocks = mock.Mock()
    mocks.attach_mock(mock_lock, 'lock')
    mocks.attach_mock(mock_logger, 'logger')
    mocks.attach_mock(mock_ip_forwarding, 'forwarding')
    mocks.attach_mock(mock_network_setup, 'network_setup')
    mocks.attach_mock(mock_network_utils, 'network')
    mocks.attach_mock(mock_watcher, 'watcher')
    self.mock_setup._ExtractInterfaceMetadata.return_value = []
    mock_lock.LockFile.side_effect = IOError('Test Error')

    with mock.patch.object(
        network_daemon.NetworkDaemon, 'HandleNetworkInterfaces'):
      network_daemon.NetworkDaemon(
          ip_forwarding_enabled=False,
          proto_id='66',
          ip_aliases=None,
          target_instance_ips=None,
          dhclient_script='x',
          dhcp_command='y',
          network_setup_enabled=False,
          debug=True)
      expected_calls = [
          mock.call.logger.Logger(name=mock.ANY, debug=True, facility=mock.ANY),
          mock.call.forwarding.IpForwarding(proto_id='66', debug=True),
          mock.call.network_setup.NetworkSetup(
              debug=True, dhclient_script='x', dhcp_command='y'),
          mock.call.network.NetworkUtils(logger=mock_logger_instance),
          mock.call.watcher.MetadataWatcher(logger=mock_logger_instance),
          mock.call.lock.LockFile(network_daemon.LOCKFILE),
          mock.call.logger.Logger().warning('Test Error'),
      ]
      self.assertEqual(mocks.mock_calls, expected_calls)

  @mock.patch('google_compute_engine.networking.network_daemon.distro_utils')
  def testHandleNetworkInterfaces(self, mock_distro_utils):
    mocks = mock.Mock()
    mocks.attach_mock(self.mock_ip_forwarding, 'forwarding')
    mocks.attach_mock(self.mock_network_setup, 'network_setup')
    mocks.attach_mock(self.mock_setup, 'setup')
    mocks.attach_mock(mock_distro_utils, 'distro_utils')
    self.mock_setup.ip_aliases = None
    self.mock_setup.target_instance_ips = None
    self.mock_setup.ip_forwarding_enabled = True
    self.mock_setup.network_setup_enabled = True
    self.mock_setup._ExtractInterfaceMetadata.return_value = [
        network_daemon.NetworkDaemon.NetworkInterface(
            'eth0', forwarded_ips=['a'], ip='1.1.1.1', ipv6=False),
        network_daemon.NetworkDaemon.NetworkInterface('eth1'),
    ]
    self.mock_setup.distro_utils = mock.MagicMock()
    result = mock.MagicMock()

    network_daemon.NetworkDaemon.HandleNetworkInterfaces(
        self.mock_setup, result)
    expected_calls = [
        mock.call.setup._ExtractInterfaceMetadata(result['networkInterfaces']),
        mock.call.network_setup.DisableIpv6(['eth0']),
        mock.call.network_setup.EnableNetworkInterfaces(['eth1']),
        mock.call.forwarding.HandleForwardedIps(
            'eth0', ['a'], '1.1.1.1'),
        mock.call.forwarding.HandleForwardedIps('eth1', None, None),
        mock.call.setup.distro_utils.RestartNetworking(self.mock_setup.logger),
    ]
    self.assertEqual(mocks.mock_calls, expected_calls)

  def testHandleNetworkInterfacesIpv6(self):
    mocks = mock.Mock()
    mocks.attach_mock(self.mock_ip_forwarding, 'forwarding')
    mocks.attach_mock(self.mock_network_setup, 'network_setup')
    mocks.attach_mock(self.mock_setup, 'setup')
    self.mock_setup.ip_aliases = None
    self.mock_setup.target_instance_ips = None
    self.mock_setup.ip_forwarding_enabled = True
    self.mock_setup.network_setup_enabled = True
    self.mock_setup._ExtractInterfaceMetadata.return_value = [
        network_daemon.NetworkDaemon.NetworkInterface(
            'eth0', forwarded_ips=['a'], ip='1.1.1.1', ipv6=True),
    ]
    self.mock_setup.distro_utils = mock.MagicMock()
    result = mock.MagicMock()

    network_daemon.NetworkDaemon.HandleNetworkInterfaces(
        self.mock_setup, result)
    expected_calls = [
        mock.call.setup._ExtractInterfaceMetadata(result['networkInterfaces']),
        mock.call.network_setup.EnableIpv6(['eth0']),
        mock.call.network_setup.EnableNetworkInterfaces([]),
        mock.call.forwarding.HandleForwardedIps(
            'eth0', ['a'], '1.1.1.1'),
        mock.call.setup.distro_utils.RestartNetworking(self.mock_setup.logger),
    ]
    self.assertEqual(mocks.mock_calls, expected_calls)

  def testHandleNetworkInterfacesIpv6Disabled(self):
    mocks = mock.Mock()
    mocks.attach_mock(self.mock_ip_forwarding, 'forwarding')
    mocks.attach_mock(self.mock_network_setup, 'network_setup')
    mocks.attach_mock(self.mock_setup, 'setup')
    self.mock_setup.ip_aliases = None
    self.mock_setup.target_instance_ips = None
    self.mock_setup.ip_forwarding_enabled = True
    self.mock_setup.network_setup_enabled = True
    self.mock_setup._ExtractInterfaceMetadata.return_value = [
        network_daemon.NetworkDaemon.NetworkInterface(
            'eth0', forwarded_ips=['a'], ip='1.1.1.1', ipv6=False),
    ]
    self.mock_setup.distro_utils = mock.MagicMock()
    result = mock.MagicMock()

    network_daemon.NetworkDaemon.HandleNetworkInterfaces(
        self.mock_setup, result)
    expected_calls = [
        mock.call.setup._ExtractInterfaceMetadata(result['networkInterfaces']),
        mock.call.network_setup.DisableIpv6(['eth0']),
        mock.call.network_setup.EnableNetworkInterfaces([]),
        mock.call.forwarding.HandleForwardedIps(
            'eth0', ['a'], '1.1.1.1'),
        mock.call.setup.distro_utils.RestartNetworking(self.mock_setup.logger),
    ]
    self.assertEqual(mocks.mock_calls, expected_calls)

  def testHandleNetworkInterfacesDisabled(self):
    mocks = mock.Mock()
    mocks.attach_mock(self.mock_ip_forwarding, 'forwarding')
    mocks.attach_mock(self.mock_network_setup, 'network_setup')
    mocks.attach_mock(self.mock_setup, 'setup')
    self.mock_setup.ip_aliases = None
    self.mock_setup.target_instance_ips = None
    self.mock_setup.ip_forwarding_enabled = False
    self.mock_setup.network_setup_enabled = False
    self.mock_setup._ExtractInterfaceMetadata.return_value = [
        network_daemon.NetworkDaemon.NetworkInterface('a'),
        network_daemon.NetworkDaemon.NetworkInterface('b'),
    ]
    self.mock_setup.distro_utils = mock.MagicMock()
    result = mock.MagicMock()

    network_daemon.NetworkDaemon.HandleNetworkInterfaces(
        self.mock_setup, result)
    expected_calls = [
        mock.call.setup._ExtractInterfaceMetadata(result['networkInterfaces']),
        mock.call.setup.distro_utils.RestartNetworking(self.mock_setup.logger),
    ]
    self.assertEqual(mocks.mock_calls, expected_calls)

  def testExtractInterfaceMetadata(self):
    self.mock_setup.ip_aliases = True
    self.mock_setup.target_instance_ips = True
    self.mock_setup.network_utils = network_utils.NetworkUtils()
    self.mock_setup.network_utils.interfaces = {
        '1': 'eth0', '2': 'eth1', '3': 'eth2',
    }
    metadata = [
        {
            'mac': '1',
            'forwardedIps': ['a'],
            'dhcpv6Refresh': 1,
        },
        {
            'mac': '2',
            'forwardedIps': ['b'],
            'ipAliases': ['banana'],
            'targetInstanceIps': ['baklava'],
            'ip': '2.2.2.2',
            'dhcpv6Refresh': 2,
        },
        {
            'mac': '3',
            'ipAliases': ['cherry'],
            'targetInstanceIps': ['cake'],
        },
        {
            'mac': '4',
        },
        {
            'forwardedIps': ['d'],
            'ipAliases': ['date'],
            'targetInstanceIps': ['doughnuts'],
        },
    ]
    expected_interfaces = [
        network_daemon.NetworkDaemon.NetworkInterface(
            'eth0', forwarded_ips=['a'], ip=None, ipv6=True),
        network_daemon.NetworkDaemon.NetworkInterface(
            'eth1', forwarded_ips=['b', 'banana', 'baklava'], ip='2.2.2.2',
            ipv6=True),
        network_daemon.NetworkDaemon.NetworkInterface(
            'eth2', forwarded_ips=['cherry', 'cake'], ip=None),
    ]

    actual_interfaces = network_daemon.NetworkDaemon._ExtractInterfaceMetadata(
        self.mock_setup, metadata)
    for actual, expected in zip(actual_interfaces, expected_interfaces):
      self.assertEqual(actual.name, expected.name)
      self.assertEqual(actual.forwarded_ips, expected.forwarded_ips)
      self.assertEqual(actual.ip, expected.ip)
      self.assertEqual(actual.ipv6, expected.ipv6)

  def testExtractInterfaceMetadataWithoutOptions(self):
    self.mock_setup.ip_aliases = None
    self.mock_setup.target_instance_ips = None
    self.mock_setup.network_utils = network_utils.NetworkUtils()
    self.mock_setup.network_utils.interfaces = {
        '1': 'eth0', '2': 'eth1', '3': 'eth2',
    }
    metadata = [
        {
            'mac': '1',
            'forwardedIps': ['a'],
            'dhcpv6Refresh': 1,
        },
        {
            'mac': '2',
            'forwardedIps': ['b'],
            'ipAliases': ['banana'],
            'targetInstanceIps': ['baklava'],
            'ip': '2.2.2.2',
            'dhcpv6Refresh': 2,
        },
        {
            'mac': '3',
            'ipAliases': ['cherry'],
            'targetInstanceIps': ['cake'],
        },
    ]
    expected_interfaces = [
        network_daemon.NetworkDaemon.NetworkInterface(
            'eth0', forwarded_ips=['a'], ip=None, ipv6=True),
        network_daemon.NetworkDaemon.NetworkInterface(
            'eth1', forwarded_ips=['b'], ip='2.2.2.2', ipv6=True),
        network_daemon.NetworkDaemon.NetworkInterface(
            'eth2', forwarded_ips=[], ip=None, ipv6=False),
    ]

    actual_interfaces = network_daemon.NetworkDaemon._ExtractInterfaceMetadata(
        self.mock_setup, metadata)
    for actual, expected in zip(actual_interfaces, expected_interfaces):
      self.assertEqual(actual.name, expected.name)
      self.assertEqual(actual.forwarded_ips, expected.forwarded_ips)
      self.assertEqual(actual.ip, expected.ip)
      self.assertEqual(actual.ipv6, expected.ipv6)
