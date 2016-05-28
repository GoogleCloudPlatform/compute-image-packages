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

from google_compute_engine.ip_forwarding import ip_forwarding_daemon
from google_compute_engine.test_compat import mock
from google_compute_engine.test_compat import unittest


class IpForwardingDaemonTest(unittest.TestCase):

  def setUp(self):
    self.mock_logger = mock.Mock()
    self.mock_watcher = mock.Mock()
    self.mock_utils = mock.Mock()

    self.mock_setup = mock.create_autospec(
        ip_forwarding_daemon.IpForwardingDaemon)
    self.mock_setup.logger = self.mock_logger
    self.mock_setup.watcher = self.mock_watcher
    self.mock_setup.utils = self.mock_utils

  @mock.patch('google_compute_engine.ip_forwarding.ip_forwarding_daemon.ip_forwarding_utils')
  @mock.patch('google_compute_engine.ip_forwarding.ip_forwarding_daemon.metadata_watcher')
  @mock.patch('google_compute_engine.ip_forwarding.ip_forwarding_daemon.logger')
  @mock.patch('google_compute_engine.ip_forwarding.ip_forwarding_daemon.file_utils')
  def testIpForwardingDaemon(self, mock_lock, mock_logger, mock_watcher,
                             mock_utils):
    mock_logger_instance = mock.Mock()
    mock_logger.Logger.return_value = mock_logger_instance
    mocks = mock.Mock()
    mocks.attach_mock(mock_lock, 'lock')
    mocks.attach_mock(mock_logger, 'logger')
    mocks.attach_mock(mock_utils, 'utils')
    mocks.attach_mock(mock_watcher, 'watcher')
    metadata_key = ip_forwarding_daemon.IpForwardingDaemon.forwarded_ips
    with mock.patch.object(
        ip_forwarding_daemon.IpForwardingDaemon,
        'HandleForwardedIps') as mock_handle:
      ip_forwarding_daemon.IpForwardingDaemon(proto_id='66', debug=True)
      expected_calls = [
          mock.call.logger.Logger(name=mock.ANY, debug=True, facility=mock.ANY),
          mock.call.watcher.MetadataWatcher(logger=mock_logger_instance),
          mock.call.utils.IpForwardingUtils(
              logger=mock_logger_instance, proto_id='66'),
          mock.call.lock.LockFile(ip_forwarding_daemon.LOCKFILE),
          mock.call.lock.LockFile().__enter__(),
          mock.call.logger.Logger().info(mock.ANY),
          mock.call.watcher.MetadataWatcher().WatchMetadata(
              mock_handle, metadata_key=metadata_key, recursive=True),
          mock.call.lock.LockFile().__exit__(None, None, None),
      ]
      self.assertEqual(mocks.mock_calls, expected_calls)

  @mock.patch('google_compute_engine.ip_forwarding.ip_forwarding_daemon.ip_forwarding_utils')
  @mock.patch('google_compute_engine.ip_forwarding.ip_forwarding_daemon.metadata_watcher')
  @mock.patch('google_compute_engine.ip_forwarding.ip_forwarding_daemon.logger')
  @mock.patch('google_compute_engine.ip_forwarding.ip_forwarding_daemon.file_utils')
  def testIpForwardingDaemonError(self, mock_lock, mock_logger, mock_watcher,
                                  mock_utils):
    mock_logger_instance = mock.Mock()
    mock_logger.Logger.return_value = mock_logger_instance
    mocks = mock.Mock()
    mocks.attach_mock(mock_lock, 'lock')
    mocks.attach_mock(mock_logger, 'logger')
    mocks.attach_mock(mock_utils, 'utils')
    mocks.attach_mock(mock_watcher, 'watcher')
    mock_lock.LockFile.side_effect = IOError('Test Error')
    with mock.patch.object(
        ip_forwarding_daemon.IpForwardingDaemon, 'HandleForwardedIps'):
      ip_forwarding_daemon.IpForwardingDaemon()
      expected_calls = [
          mock.call.logger.Logger(
              name=mock.ANY, debug=False, facility=mock.ANY),
          mock.call.watcher.MetadataWatcher(logger=mock_logger_instance),
          mock.call.utils.IpForwardingUtils(
              logger=mock_logger_instance, proto_id=None),
          mock.call.lock.LockFile(ip_forwarding_daemon.LOCKFILE),
          mock.call.logger.Logger().warning('Test Error'),
      ]
      self.assertEqual(mocks.mock_calls, expected_calls)

  def testLogForwardedIpChanges(self):
    ip_forwarding_daemon.IpForwardingDaemon._LogForwardedIpChanges(
        self.mock_setup, [], [], [], [])
    ip_forwarding_daemon.IpForwardingDaemon._LogForwardedIpChanges(
        self.mock_setup, ['a'], ['a'], [], [])
    ip_forwarding_daemon.IpForwardingDaemon._LogForwardedIpChanges(
        self.mock_setup, ['a'], [], [], ['a'])
    ip_forwarding_daemon.IpForwardingDaemon._LogForwardedIpChanges(
        self.mock_setup, ['a', 'b'], ['b'], [], ['a'])
    ip_forwarding_daemon.IpForwardingDaemon._LogForwardedIpChanges(
        self.mock_setup, ['a'], ['b'], ['b'], ['a'])
    expected_calls = [
        mock.call.info(mock.ANY, ['a'], None, None, ['a']),
        mock.call.info(mock.ANY, ['a', 'b'], ['b'], None, ['a']),
        mock.call.info(mock.ANY, ['a'], ['b'], ['b'], ['a']),
    ]
    self.assertEqual(self.mock_logger.mock_calls, expected_calls)

  def testAddForwardedIp(self):
    ip_forwarding_daemon.IpForwardingDaemon._AddForwardedIps(
        self.mock_setup, [])
    self.assertEqual(self.mock_utils.mock_calls, [])

    ip_forwarding_daemon.IpForwardingDaemon._AddForwardedIps(
        self.mock_setup, ['a', 'b', 'c'])
    expected_calls = [
        mock.call.AddForwardedIp('a'),
        mock.call.AddForwardedIp('b'),
        mock.call.AddForwardedIp('c'),
    ]
    self.assertEqual(self.mock_utils.mock_calls, expected_calls)

  def testRemoveForwardedIp(self):
    ip_forwarding_daemon.IpForwardingDaemon._RemoveForwardedIps(
        self.mock_setup, [])
    self.assertEqual(self.mock_utils.mock_calls, [])

    ip_forwarding_daemon.IpForwardingDaemon._RemoveForwardedIps(
        self.mock_setup, ['a', 'b', 'c'])
    expected_calls = [
        mock.call.RemoveForwardedIp('a'),
        mock.call.RemoveForwardedIp('b'),
        mock.call.RemoveForwardedIp('c'),
    ]
    self.assertEqual(self.mock_utils.mock_calls, expected_calls)

  def testHandleForwardedIps(self):
    configured = ['c', 'c', 'b', 'b', 'a', 'a']
    desired = ['d', 'd', 'c']
    mocks = mock.Mock()
    mocks.attach_mock(self.mock_utils, 'utils')
    mocks.attach_mock(self.mock_setup, 'setup')
    self.mock_utils.ParseForwardedIps.return_value = desired
    self.mock_utils.GetForwardedIps.return_value = configured
    result = 'result'
    expected_add = ['d']
    expected_remove = ['a', 'b']

    ip_forwarding_daemon.IpForwardingDaemon.HandleForwardedIps(
        self.mock_setup, result)
    expected_calls = [
        mock.call.utils.ParseForwardedIps(result),
        mock.call.utils.GetForwardedIps(),
        mock.call.setup._LogForwardedIpChanges(
            configured, desired, expected_add, expected_remove),
        mock.call.setup._AddForwardedIps(expected_add),
        mock.call.setup._RemoveForwardedIps(expected_remove),
    ]
    self.assertEqual(mocks.mock_calls, expected_calls)


if __name__ == '__main__':
  unittest.main()
