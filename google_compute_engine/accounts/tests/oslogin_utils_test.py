#!/usr/bin/python
# Copyright 2017 Google Inc. All Rights Reserved.
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

"""Unittest for oslogin_utils.py module."""

import time

from google_compute_engine.accounts import oslogin_utils
from google_compute_engine.test_compat import mock
from google_compute_engine.test_compat import unittest


class OsLoginUtilsTest(unittest.TestCase):

  def setUp(self):
    self.mock_logger = mock.Mock()
    self.oslogin_control_script = 'google_oslogin_control'
    self.oslogin_nss_cache = '/etc/oslogin_passwd.cache'
    self.oslogin_nss_cache_script = 'google_oslogin_nss_cache'

    self.mock_oslogin = mock.create_autospec(oslogin_utils.OsLoginUtils)
    self.mock_oslogin.logger = self.mock_logger
    self.mock_oslogin.oslogin_installed = True
    self.mock_oslogin.update_time = 0

  @mock.patch('google_compute_engine.accounts.oslogin_utils.subprocess.call')
  def testRunOsLoginControl(self, mock_call):
    expected_return_value = 0
    mocks = mock.Mock()
    mocks.attach_mock(mock_call, 'call')
    mock_call.return_value = expected_return_value

    self.assertEqual(
        oslogin_utils.OsLoginUtils._RunOsLoginControl(
            self.mock_oslogin, 'activate'), expected_return_value)
    expected_calls = [
        mock.call.call([self.oslogin_control_script, 'activate']),
    ]
    self.assertEqual(mocks.mock_calls, expected_calls)

  @mock.patch('google_compute_engine.accounts.oslogin_utils.subprocess.call')
  def testRunOsLoginControlStatus(self, mock_call):
    expected_return_value = 3
    mocks = mock.Mock()
    mocks.attach_mock(mock_call, 'call')
    mock_call.return_value = expected_return_value

    self.assertEqual(
        oslogin_utils.OsLoginUtils._RunOsLoginControl(
            self.mock_oslogin, 'status'), expected_return_value)
    expected_calls = [
        mock.call.call([self.oslogin_control_script, 'status']),
    ]
    self.assertEqual(mocks.mock_calls, expected_calls)

  @mock.patch('google_compute_engine.accounts.oslogin_utils.subprocess.call')
  def testOsLoginNotInstalled(self, mock_call):
    mocks = mock.Mock()
    mocks.attach_mock(mock_call, 'call')
    mock_call.side_effect = OSError(2, 'Not Found')

    self.assertIsNone(
        oslogin_utils.OsLoginUtils._RunOsLoginControl(
            self.mock_oslogin, 'status'))
    expected_calls = [
        mock.call.call([self.oslogin_control_script, 'status']),
    ]
    self.assertEqual(mocks.mock_calls, expected_calls)

  @mock.patch('google_compute_engine.accounts.oslogin_utils.subprocess.call')
  def testOsLoginControlError(self, mock_call):
    mocks = mock.Mock()
    mocks.attach_mock(mock_call, 'call')
    mock_call.side_effect = OSError

    with self.assertRaises(OSError):
      oslogin_utils.OsLoginUtils._RunOsLoginControl(self.mock_oslogin, 'status')
    expected_calls = [
        mock.call.call([self.oslogin_control_script, 'status']),
    ]
    self.assertEqual(mocks.mock_calls, expected_calls)

  @mock.patch('google_compute_engine.accounts.oslogin_utils.os.path.exists')
  def testGetStatusActive(self, mock_exists):
    mocks = mock.Mock()
    mocks.attach_mock(mock_exists, 'exists')
    self.mock_oslogin._RunOsLoginControl.return_value = 0
    mock_exists.return_value = True

    self.assertTrue(oslogin_utils.OsLoginUtils._GetStatus(self.mock_oslogin))
    expected_calls = [mock.call.exists(self.oslogin_nss_cache)]
    self.assertEqual(mocks.mock_calls, expected_calls)

  @mock.patch('google_compute_engine.accounts.oslogin_utils.os.path.exists')
  def testGetStatusNotActive(self, mock_exists):
    mocks = mock.Mock()
    mocks.attach_mock(mock_exists, 'exists')
    self.mock_oslogin._RunOsLoginControl.return_value = 3
    mock_exists.return_value = True

    self.assertFalse(oslogin_utils.OsLoginUtils._GetStatus(self.mock_oslogin))
    expected_calls = [mock.call.exists(self.oslogin_nss_cache)]
    self.assertEqual(mocks.mock_calls, expected_calls)

  @mock.patch('google_compute_engine.accounts.oslogin_utils.os.path.exists')
  def testGetStatusNoCache(self, mock_exists):
    mocks = mock.Mock()
    mocks.attach_mock(mock_exists, 'exists')
    self.mock_oslogin._RunOsLoginControl.return_value = 0
    mock_exists.return_value = False

    self.assertFalse(oslogin_utils.OsLoginUtils._GetStatus(self.mock_oslogin))
    expected_calls = [mock.call.exists(self.oslogin_nss_cache)]
    self.assertEqual(mocks.mock_calls, expected_calls)

  def testGetStatusNotInstalled(self):
    mocks = mock.Mock()
    self.mock_oslogin._RunOsLoginControl.return_value = None
    mocks.attach_mock(self.mock_logger, 'logger')

    self.assertTrue(self.mock_oslogin.oslogin_installed)
    self.assertFalse(oslogin_utils.OsLoginUtils._GetStatus(self.mock_oslogin))
    self.assertFalse(self.mock_oslogin.oslogin_installed)
    self.assertFalse(oslogin_utils.OsLoginUtils._GetStatus(self.mock_oslogin))
    # Should only log once, even though called twice.
    expected_calls = [
        mock.call.logger.warning(mock.ANY),
    ]
    self.assertEqual(mocks.mock_calls, expected_calls)

  @mock.patch('google_compute_engine.accounts.oslogin_utils.subprocess.call')
  def testRunOsLoginNssCache(self, mock_call):
    expected_return_value = 0
    mocks = mock.Mock()
    mocks.attach_mock(mock_call, 'call')
    mock_call.return_value = expected_return_value

    self.assertEqual(
        oslogin_utils.OsLoginUtils._RunOsLoginNssCache(self.mock_oslogin),
        expected_return_value)
    expected_calls = [
        mock.call.call([self.oslogin_nss_cache_script]),
    ]
    self.assertEqual(mocks.mock_calls, expected_calls)

  @mock.patch('google_compute_engine.accounts.oslogin_utils.subprocess.call')
  def testRunOsLoginNssCacheNotInstalled(self, mock_call):
    mocks = mock.Mock()
    mocks.attach_mock(mock_call, 'call')
    mock_call.side_effect = OSError(2, 'Not Found')

    self.assertIsNone(
        oslogin_utils.OsLoginUtils._RunOsLoginNssCache(self.mock_oslogin))
    expected_calls = [
        mock.call.call([self.oslogin_nss_cache_script]),
    ]
    self.assertEqual(mocks.mock_calls, expected_calls)

  @mock.patch('google_compute_engine.accounts.oslogin_utils.subprocess.call')
  def testRunOsLoginNssCacheError(self, mock_call):
    mocks = mock.Mock()
    mocks.attach_mock(mock_call, 'call')
    mock_call.side_effect = OSError

    with self.assertRaises(OSError):
      oslogin_utils.OsLoginUtils._RunOsLoginNssCache(self.mock_oslogin)
    expected_calls = [
        mock.call.call([self.oslogin_nss_cache_script]),
    ]
    self.assertEqual(mocks.mock_calls, expected_calls)

  @mock.patch('google_compute_engine.accounts.oslogin_utils.os.remove')
  @mock.patch('google_compute_engine.accounts.oslogin_utils.os.path.exists')
  def testRemoveOsLoginNssCache(self, mock_exists, mock_remove):
    mock_exists.return_value = True

    oslogin_utils.OsLoginUtils._RemoveOsLoginNssCache(self.mock_oslogin)
    mock_exists.assert_called_once_with(self.oslogin_nss_cache)
    mock_remove.assert_called_once_with(self.oslogin_nss_cache)

  @mock.patch('google_compute_engine.accounts.oslogin_utils.os.remove')
  @mock.patch('google_compute_engine.accounts.oslogin_utils.os.path.exists')
  def testRemoveOsLoginNssCacheNotFound(self, mock_exists, mock_remove):
    mock_exists.return_value = False

    oslogin_utils.OsLoginUtils._RemoveOsLoginNssCache(self.mock_oslogin)
    mock_exists.assert_called_once_with(self.oslogin_nss_cache)
    mock_remove.assert_not_called()

  @mock.patch('google_compute_engine.accounts.oslogin_utils.os.remove')
  @mock.patch('google_compute_engine.accounts.oslogin_utils.os.path.exists')
  def testRemoveOsLoginNssCacheNotInstalled(self, mock_exists, mock_remove):
    mock_exists.return_value = True
    mock_remove.side_effect = OSError(2, 'Not Found')

    oslogin_utils.OsLoginUtils._RemoveOsLoginNssCache(self.mock_oslogin)
    mock_exists.assert_called_once_with(self.oslogin_nss_cache)
    mock_remove.assert_called_once_with(self.oslogin_nss_cache)

  @mock.patch('google_compute_engine.accounts.oslogin_utils.os.remove')
  @mock.patch('google_compute_engine.accounts.oslogin_utils.os.path.exists')
  def testRemoveOsLoginNssCacheError(self, mock_exists, mock_remove):
    mock_exists.return_value = True
    mock_remove.side_effect = OSError

    with self.assertRaises(OSError):
      oslogin_utils.OsLoginUtils._RemoveOsLoginNssCache(self.mock_oslogin)

  def testUpdateOsLoginActivate(self):
    mocks = mock.Mock()
    mocks.attach_mock(self.mock_logger, 'logger')
    mocks.attach_mock(self.mock_oslogin, 'oslogin')
    self.mock_oslogin._RunOsLoginControl.return_value = 0
    self.mock_oslogin._GetStatus.return_value = False

    oslogin_utils.OsLoginUtils.UpdateOsLogin(self.mock_oslogin, True)
    expected_calls = [
        mock.call.oslogin._GetStatus(),
        mock.call.logger.info(mock.ANY),
        mock.call.oslogin._RunOsLoginControl('activate'),
        mock.call.oslogin._RunOsLoginNssCache(),
    ]
    self.assertEqual(mocks.mock_calls, expected_calls)

  def testUpdateOsLoginDeactivate(self):
    mocks = mock.Mock()
    mocks.attach_mock(self.mock_logger, 'logger')
    mocks.attach_mock(self.mock_oslogin, 'oslogin')
    self.mock_oslogin._RunOsLoginControl.return_value = 0
    self.mock_oslogin._GetStatus.return_value = True

    oslogin_utils.OsLoginUtils.UpdateOsLogin(self.mock_oslogin, False)
    expected_calls = [
        mock.call.oslogin._GetStatus(),
        mock.call.logger.info(mock.ANY),
        mock.call.oslogin._RunOsLoginControl('deactivate'),
        mock.call.oslogin._RemoveOsLoginNssCache(),
    ]
    self.assertEqual(mocks.mock_calls, expected_calls)

  @mock.patch('time.time')
  def testUpdateOsLoginUpdateCache(self, mock_time):
    mocks = mock.Mock()
    mocks.attach_mock(self.mock_oslogin, 'oslogin')
    self.mock_oslogin._RunOsLoginControl.return_value = 0
    self.mock_oslogin._GetStatus.return_value = True
    mock_time.return_value = 6 * 60 * 60 + 1

    oslogin_utils.OsLoginUtils.UpdateOsLogin(self.mock_oslogin, True)
    expected_calls = [
        mock.call.oslogin._GetStatus(),
        mock.call.oslogin._RunOsLoginNssCache(),
    ]
    self.assertEqual(mocks.mock_calls, expected_calls)

  @mock.patch('time.time')
  def testUpdateOsLoginRedundantActivate(self, mock_time):
    mocks = mock.Mock()
    mocks.attach_mock(self.mock_oslogin, 'oslogin')
    self.mock_oslogin._RunOsLoginControl.return_value = 0
    self.mock_oslogin._GetStatus.return_value = True
    mock_time.return_value = 6 * 60 * 60

    oslogin_utils.OsLoginUtils.UpdateOsLogin(self.mock_oslogin, True)
    expected_calls = [
        mock.call.oslogin._GetStatus(),
    ]
    self.assertEqual(mocks.mock_calls, expected_calls)

  def testUpdateOsLoginRedundantDeactivate(self):
    mocks = mock.Mock()
    mocks.attach_mock(self.mock_oslogin, 'oslogin')
    self.mock_oslogin._RunOsLoginControl.return_value = 0
    self.mock_oslogin._GetStatus.return_value = False

    oslogin_utils.OsLoginUtils.UpdateOsLogin(self.mock_oslogin, False)
    expected_calls = [
        mock.call.oslogin._GetStatus(),
    ]
    self.assertEqual(mocks.mock_calls, expected_calls)

  def testUpdateOsLoginNotInstalled(self):
    mocks = mock.Mock()
    mocks.attach_mock(self.mock_oslogin, 'oslogin')
    self.mock_oslogin._RunOsLoginControl.return_value = 0
    self.mock_oslogin._GetStatus.return_value = None

    oslogin_utils.OsLoginUtils.UpdateOsLogin(self.mock_oslogin, True)
    expected_calls = [
        mock.call.oslogin._GetStatus(),
    ]
    self.assertEqual(mocks.mock_calls, expected_calls)


if __name__ == '__main__':
  unittest.main()
