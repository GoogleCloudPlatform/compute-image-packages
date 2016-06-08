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

"""Unittest for clock_skew_daemon.py module."""

import subprocess

from google_compute_engine.clock_skew import clock_skew_daemon
from google_compute_engine.test_compat import mock
from google_compute_engine.test_compat import unittest


class ClockSkewDaemonTest(unittest.TestCase):

  @mock.patch('google_compute_engine.clock_skew.clock_skew_daemon.metadata_watcher')
  @mock.patch('google_compute_engine.clock_skew.clock_skew_daemon.logger.Logger')
  @mock.patch('google_compute_engine.clock_skew.clock_skew_daemon.file_utils.LockFile')
  def testClockSkewDaemon(self, mock_lock, mock_logger, mock_watcher):
    mocks = mock.Mock()
    mocks.attach_mock(mock_lock, 'lock')
    mocks.attach_mock(mock_logger, 'logger')
    mocks.attach_mock(mock_watcher, 'watcher')
    metadata_key = clock_skew_daemon.ClockSkewDaemon.drift_token
    mock_logger.return_value = mock_logger
    mock_watcher.MetadataWatcher.return_value = mock_watcher
    with mock.patch.object(
        clock_skew_daemon.ClockSkewDaemon, 'HandleClockSync') as mock_handle:
      clock_skew_daemon.ClockSkewDaemon()
      expected_calls = [
          mock.call.logger(name=mock.ANY, debug=False, facility=mock.ANY),
          mock.call.watcher.MetadataWatcher(logger=mock_logger),
          mock.call.lock(clock_skew_daemon.LOCKFILE),
          mock.call.lock().__enter__(),
          mock.call.logger.info(mock.ANY),
          mock.call.watcher.WatchMetadata(
              mock_handle, metadata_key=metadata_key, recursive=False),
          mock.call.lock().__exit__(None, None, None),
      ]
      self.assertEqual(mocks.mock_calls, expected_calls)

  @mock.patch('google_compute_engine.clock_skew.clock_skew_daemon.metadata_watcher')
  @mock.patch('google_compute_engine.clock_skew.clock_skew_daemon.logger.Logger')
  @mock.patch('google_compute_engine.clock_skew.clock_skew_daemon.file_utils.LockFile')
  def testClockSkewDaemonError(self, mock_lock, mock_logger, mock_watcher):
    mocks = mock.Mock()
    mocks.attach_mock(mock_lock, 'lock')
    mocks.attach_mock(mock_logger, 'logger')
    mocks.attach_mock(mock_watcher, 'watcher')
    mock_lock.side_effect = IOError('Test Error')
    mock_logger.return_value = mock_logger
    with mock.patch.object(
        clock_skew_daemon.ClockSkewDaemon, 'HandleClockSync'):
      clock_skew_daemon.ClockSkewDaemon(debug=True)
      expected_calls = [
          mock.call.logger(name=mock.ANY, debug=True, facility=mock.ANY),
          mock.call.watcher.MetadataWatcher(logger=mock_logger),
          mock.call.lock(clock_skew_daemon.LOCKFILE),
          mock.call.logger.warning('Test Error'),
      ]
      self.assertEqual(mocks.mock_calls, expected_calls)

  @mock.patch('google_compute_engine.clock_skew.clock_skew_daemon.subprocess.check_call')
  def testHandleClockSync(self, mock_call):
    command = ['/sbin/hwclock', '--hctosys']
    mock_sync = mock.create_autospec(clock_skew_daemon.ClockSkewDaemon)
    mock_logger = mock.Mock()
    mock_sync.logger = mock_logger

    clock_skew_daemon.ClockSkewDaemon.HandleClockSync(mock_sync, 'Response')
    mock_call.assert_called_once_with(command)
    expected_calls = [
        mock.call.info(mock.ANY, 'Response'),
        mock.call.info(mock.ANY),
    ]
    self.assertEqual(mock_logger.mock_calls, expected_calls)

  @mock.patch('google_compute_engine.clock_skew.clock_skew_daemon.subprocess.check_call')
  def testHandleClockSyncError(self, mock_call):
    command = ['/sbin/hwclock', '--hctosys']
    mock_sync = mock.create_autospec(clock_skew_daemon.ClockSkewDaemon)
    mock_logger = mock.Mock()
    mock_sync.logger = mock_logger
    mock_call.side_effect = subprocess.CalledProcessError(1, 'Test')

    clock_skew_daemon.ClockSkewDaemon.HandleClockSync(mock_sync, 'Response')
    mock_call.assert_called_once_with(command)
    expected_calls = [
        mock.call.info(mock.ANY, 'Response'),
        mock.call.warning(mock.ANY),
    ]
    self.assertEqual(mock_logger.mock_calls, expected_calls)


if __name__ == '__main__':
  unittest.main()
