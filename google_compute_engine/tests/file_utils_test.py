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

"""Unittest for file_utils.py module."""

from google_compute_engine import file_utils
from google_compute_engine.test_compat import mock
from google_compute_engine.test_compat import unittest


class FileUtilsTest(unittest.TestCase):

  def setUp(self):
    self.fd = 1
    self.path = '/tmp/path'

  @mock.patch('google_compute_engine.file_utils.subprocess.call')
  @mock.patch('google_compute_engine.file_utils.os.access')
  @mock.patch('google_compute_engine.file_utils.os.path.isfile')
  def testSetSELinuxContext(self, mock_isfile, mock_access, mock_call):
    restorecon = '/sbin/restorecon'
    path = 'path'
    mock_isfile.return_value = True
    mock_access.return_value = True
    file_utils._SetSELinuxContext(path)
    mock_isfile.assert_called_once_with(restorecon)
    mock_access.assert_called_once_with(restorecon, file_utils.os.X_OK)
    mock_call.assert_called_once_with([restorecon, path])

  @mock.patch('google_compute_engine.file_utils.subprocess.call')
  @mock.patch('google_compute_engine.file_utils.os.access')
  @mock.patch('google_compute_engine.file_utils.os.path.isfile')
  def testSetSELinuxContextSkip(self, mock_isfile, mock_access, mock_call):
    mock_isfile.side_effect = [True, False, False]
    mock_access.side_effect = [False, True, False]
    file_utils._SetSELinuxContext('1')
    file_utils._SetSELinuxContext('2')
    file_utils._SetSELinuxContext('3')
    mock_call.assert_not_called()

  @mock.patch('google_compute_engine.file_utils._SetSELinuxContext')
  @mock.patch('google_compute_engine.file_utils.os.path.exists')
  @mock.patch('google_compute_engine.file_utils.os.mkdir')
  @mock.patch('google_compute_engine.file_utils.os.chown')
  @mock.patch('google_compute_engine.file_utils.os.chmod')
  def testSetPermissions(
      self, mock_chmod, mock_chown, mock_mkdir, mock_exists, mock_context):
    mocks = mock.Mock()
    mocks.attach_mock(mock_chmod, 'chmod')
    mocks.attach_mock(mock_chown, 'chown')
    mocks.attach_mock(mock_mkdir, 'mkdir')
    mocks.attach_mock(mock_exists, 'exists')
    mocks.attach_mock(mock_context, 'context')
    path = 'path'
    mode = 'mode'
    uid = 'uid'
    gid = 'gid'
    mock_exists.side_effect = [False, True, False]

    # Create a new directory.
    file_utils.SetPermissions(path, mode=mode, uid=uid, gid=gid, mkdir=True)
    # The path exists, so do not create a new directory.
    file_utils.SetPermissions(path, mode=mode, uid=uid, gid=gid, mkdir=True)
    # Create a new directory without a mode specified.
    file_utils.SetPermissions(path, uid=uid, gid=gid, mkdir=True)
    # Do not create the path even though it does not exist.
    file_utils.SetPermissions(path, mode=mode, uid=uid, gid=gid, mkdir=False)
    # Do not set an owner when a UID or GID is not specified.
    file_utils.SetPermissions(path, mode=mode, mkdir=False)
    # Set the SELinux context when no parameters are specified.
    file_utils.SetPermissions(path)
    expected_calls = [
        # Create a new directory.
        mock.call.exists(path),
        mock.call.mkdir(path, mode),
        mock.call.chown(path, uid, gid),
        mock.call.context(path),
        # Attempt to create a new path but reuse existing path.
        mock.call.exists(path),
        mock.call.chmod(path, mode),
        mock.call.chown(path, uid, gid),
        mock.call.context(path),
        # Create a new directory with default mode.
        mock.call.exists(path),
        mock.call.mkdir(path, 0o777),
        mock.call.chown(path, uid, gid),
        mock.call.context(path),
        # Set permissions and owner on an existing path.
        mock.call.chmod(path, mode),
        mock.call.chown(path, uid, gid),
        mock.call.context(path),
        # Set permissions, without changing ownership, of an existing path.
        mock.call.chmod(path, mode),
        mock.call.context(path),
        # Set SELinux context on an existing path.
        mock.call.context(path),
    ]
    self.assertEqual(mocks.mock_calls, expected_calls)

  @mock.patch('google_compute_engine.file_utils.fcntl.flock')
  def testLock(self, mock_flock):
    operation = file_utils.fcntl.LOCK_EX | file_utils.fcntl.LOCK_NB
    file_utils.Lock(self.fd, self.path, False)
    mock_flock.assert_called_once_with(self.fd, operation)

  @mock.patch('google_compute_engine.file_utils.fcntl.flock')
  def testLockBlocking(self, mock_flock):
    operation = file_utils.fcntl.LOCK_EX
    file_utils.Lock(self.fd, self.path, True)
    mock_flock.assert_called_once_with(self.fd, operation)

  @mock.patch('google_compute_engine.file_utils.fcntl.flock')
  def testLockTakenException(self, mock_flock):
    error = IOError('Test Error')
    error.errno = file_utils.errno.EWOULDBLOCK
    mock_flock.side_effect = error
    try:
      file_utils.Lock(self.fd, self.path, False)
    except IOError as e:
      self.assertTrue(self.path in str(e))

  @mock.patch('google_compute_engine.file_utils.fcntl.flock')
  def testLockException(self, mock_flock):
    error = IOError('Test Error')
    mock_flock.side_effect = error
    try:
      file_utils.Lock(self.fd, self.path, False)
    except IOError as e:
      self.assertTrue(self.path in str(e))
      self.assertTrue('Test Error' in str(e))

  @mock.patch('google_compute_engine.file_utils.fcntl.flock')
  def testUnlock(self, mock_flock):
    operation = file_utils.fcntl.LOCK_UN | file_utils.fcntl.LOCK_NB
    file_utils.Unlock(self.fd, self.path)
    mock_flock.assert_called_once_with(self.fd, operation)

  @mock.patch('google_compute_engine.file_utils.fcntl.flock')
  def testUnlockTakenException(self, mock_flock):
    error = IOError('Test Error')
    error.errno = file_utils.errno.EWOULDBLOCK
    mock_flock.side_effect = error
    try:
      file_utils.Unlock(self.fd, self.path)
    except IOError as e:
      self.assertTrue(self.path in str(e))

  @mock.patch('google_compute_engine.file_utils.fcntl.flock')
  def testUnlockException(self, mock_flock):
    error = IOError('Test Error')
    mock_flock.side_effect = error
    try:
      file_utils.Unlock(self.fd, self.path)
    except IOError as e:
      self.assertTrue(self.path in str(e))
      self.assertTrue('Test Error' in str(e))

  @mock.patch('google_compute_engine.file_utils.Unlock')
  @mock.patch('google_compute_engine.file_utils.Lock')
  @mock.patch('google_compute_engine.file_utils.os')
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

    with file_utils.LockFile(self.path, blocking=True):
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
