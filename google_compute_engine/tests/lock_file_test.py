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

"""Unittest for lock_file_test.py module."""

from google_compute_engine import lock_file
from google_compute_engine.test_compat import mock
from google_compute_engine.test_compat import unittest


class LockFileTest(unittest.TestCase):

  def setUp(self):
    self.fd = 1
    self.path = '/tmp/path'

  @mock.patch('google_compute_engine.lock_file.fcntl.flock')
  def testLock(self, mock_flock):
    operation = lock_file.fcntl.LOCK_EX | lock_file.fcntl.LOCK_NB
    lock_file.Lock(self.fd, self.path, False)
    mock_flock.assert_called_once_with(self.fd, operation)

  @mock.patch('google_compute_engine.lock_file.fcntl.flock')
  def testLockBlocking(self, mock_flock):
    operation = lock_file.fcntl.LOCK_EX
    lock_file.Lock(self.fd, self.path, True)
    mock_flock.assert_called_once_with(self.fd, operation)

  @mock.patch('google_compute_engine.lock_file.fcntl.flock')
  def testLockTakenException(self, mock_flock):
    error = IOError('Test Error')
    error.errno = lock_file.errno.EWOULDBLOCK
    mock_flock.side_effect = error
    try:
      lock_file.Lock(self.fd, self.path, False)
    except IOError as e:
      self.assertTrue(self.path in str(e))

  @mock.patch('google_compute_engine.lock_file.fcntl.flock')
  def testLockException(self, mock_flock):
    error = IOError('Test Error')
    mock_flock.side_effect = error
    try:
      lock_file.Lock(self.fd, self.path, False)
    except IOError as e:
      self.assertTrue(self.path in str(e))
      self.assertTrue('Test Error' in str(e))

  @mock.patch('google_compute_engine.lock_file.fcntl.flock')
  def testUnlock(self, mock_flock):
    operation = lock_file.fcntl.LOCK_UN | lock_file.fcntl.LOCK_NB
    lock_file.Unlock(self.fd, self.path)
    mock_flock.assert_called_once_with(self.fd, operation)

  @mock.patch('google_compute_engine.lock_file.fcntl.flock')
  def testUnlockTakenException(self, mock_flock):
    error = IOError('Test Error')
    error.errno = lock_file.errno.EWOULDBLOCK
    mock_flock.side_effect = error
    try:
      lock_file.Unlock(self.fd, self.path)
    except IOError as e:
      self.assertTrue(self.path in str(e))

  @mock.patch('google_compute_engine.lock_file.fcntl.flock')
  def testUnlockException(self, mock_flock):
    error = IOError('Test Error')
    mock_flock.side_effect = error
    try:
      lock_file.Unlock(self.fd, self.path)
    except IOError as e:
      self.assertTrue(self.path in str(e))
      self.assertTrue('Test Error' in str(e))

  @mock.patch('google_compute_engine.lock_file.Unlock')
  @mock.patch('google_compute_engine.lock_file.Lock')
  @mock.patch('google_compute_engine.lock_file.os')
  def testLockFile(self, mock_os, mock_lock, mock_unlock):
    mock_callable = mock.Mock()
    mock_os.open.return_value = self.fd
    mock_os.O_CREAT = 1
    mocks = mock.Mock()
    mocks.attach_mock(mock_callable, 'callable')
    mocks.attach_mock(mock_lock, 'lock')
    mocks.attach_mock(mock_unlock, 'unlock')
    mocks.attach_mock(mock_os.open, 'open')
    mocks.attach_mock(mock_os.close, 'close')

    with lock_file.LockFile(self.path, blocking=True):
      mock_callable('test')

    expected_calls = [
        mock.call.open(self.path, 1),
        mock.call.lock(self.fd, self.path, True),
        mock.call.callable('test'),
        mock.call.unlock(self.fd, self.path),
        mock.call.close(1),
    ]
    self.assertEqual(mocks.mock_calls, expected_calls)


if __name__ == '__main__':
  unittest.main()
