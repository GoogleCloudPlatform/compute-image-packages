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

import itertools

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
            self.mock_oslogin, ['activate']), expected_return_value)
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
            self.mock_oslogin, ['status']), expected_return_value)
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
            self.mock_oslogin, ['status']))
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
      oslogin_utils.OsLoginUtils._RunOsLoginControl(
          self.mock_oslogin, ['status'])
    expected_calls = [
        mock.call.call([self.oslogin_control_script, 'status']),
    ]
    self.assertEqual(mocks.mock_calls, expected_calls)

  @mock.patch('google_compute_engine.accounts.oslogin_utils.os.path.exists')
  def testGetStatusActive(self, mock_exists):
    mocks = mock.Mock()
    mocks.attach_mock(mock_exists, 'exists')
    mocks.attach_mock(self.mock_oslogin, 'oslogin')
    self.mock_oslogin._RunOsLoginControl.return_value = 0
    mock_exists.return_value = True

    self.assertTrue(
        oslogin_utils.OsLoginUtils._GetStatus(
            self.mock_oslogin, two_factor=False))
    expected_calls = [
        mock.call.oslogin._RunOsLoginControl(['status']),
        mock.call.exists(self.oslogin_nss_cache),
    ]
    self.assertEqual(mocks.mock_calls, expected_calls)

  @mock.patch('google_compute_engine.accounts.oslogin_utils.os.path.exists')
  def testGetStatusNotActive(self, mock_exists):
    mocks = mock.Mock()
    mocks.attach_mock(mock_exists, 'exists')
    mocks.attach_mock(self.mock_oslogin, 'oslogin')
    self.mock_oslogin._RunOsLoginControl.return_value = 3
    mock_exists.return_value = True

    self.assertFalse(
        oslogin_utils.OsLoginUtils._GetStatus(
            self.mock_oslogin, two_factor=True))
    expected_calls = [
        mock.call.oslogin._RunOsLoginControl(['status', '--twofactor']),
        mock.call.exists(self.oslogin_nss_cache),
    ]
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

  @mock.patch('time.time')
  def testUpdateOsLoginUpdateCache(self, mock_time):
    mocks = mock.Mock()
    mocks.attach_mock(self.mock_oslogin, 'oslogin')
    self.mock_oslogin._RunOsLoginControl.return_value = 0
    self.mock_oslogin._GetStatus.return_value = True
    mock_time.return_value = 6 * 60 * 60 + 1

    oslogin_utils.OsLoginUtils.UpdateOsLogin(
        self.mock_oslogin, True, two_factor_desired=True)
    expected_calls = [
        mock.call.oslogin._GetStatus(two_factor=False),
        mock.call.oslogin._GetStatus(two_factor=True),
        mock.call.oslogin._RunOsLoginNssCache(),
    ]
    self.assertEqual(mocks.mock_calls, expected_calls)

  @mock.patch('time.time')
  def testUpdateOsLogin(self, mock_time):

    def _AssertNoUpdate():
      expected_calls = [
          mock.call.oslogin._GetStatus(two_factor=False),
          mock.call.oslogin._GetStatus(two_factor=True),
      ]
      self.assertEqual(mocks.mock_calls, expected_calls)
      self.assertEqual(return_value, 0)

    def _AssertActivated(two_factor=False):
      params = ['activate', '--twofactor'] if two_factor else ['activate']
      expected_calls = [
          mock.call.oslogin._GetStatus(two_factor=False),
          mock.call.oslogin._GetStatus(two_factor=True),
          mock.call.logger.info(mock.ANY),
          mock.call.oslogin._RunOsLoginControl(params),
          mock.call.oslogin._RunOsLoginNssCache(),
      ]
      self.assertEqual(mocks.mock_calls, expected_calls)

    def _AssertDeactivated():
      expected_calls = [
          mock.call.oslogin._GetStatus(two_factor=False),
          mock.call.oslogin._GetStatus(two_factor=True),
          mock.call.logger.info(mock.ANY),
          mock.call.oslogin._RunOsLoginControl(['deactivate']),
          mock.call.oslogin._RemoveOsLoginNssCache(),
      ]
      self.assertEqual(mocks.mock_calls, expected_calls)

    def _AssertReactivated():
      expected_calls = [
          mock.call.oslogin._GetStatus(two_factor=False),
          mock.call.oslogin._GetStatus(two_factor=True),
          mock.call.logger.info(mock.ANY),
          mock.call.oslogin._RunOsLoginControl(['deactivate']),
          mock.call.oslogin._RunOsLoginControl(['activate']),
      ]
      self.assertEqual(mocks.mock_calls, expected_calls)

    parameters = list(itertools.product([False, True], repeat=4))
    for (oslogin, two_factor, oslogin_config, two_factor_config) in parameters:
      mocks = mock.Mock()
      mocks.attach_mock(self.mock_logger, 'logger')
      mocks.attach_mock(self.mock_oslogin, 'oslogin')
      self.mock_oslogin._RunOsLoginControl.return_value = 0
      self.mock_oslogin._GetStatus.side_effect = [
          oslogin_config, two_factor_config]
      mock_time.return_value = 6 * 60 * 60
      return_value = oslogin_utils.OsLoginUtils.UpdateOsLogin(
          self.mock_oslogin, oslogin, two_factor_desired=two_factor)

      if oslogin_config:
        if not oslogin:
          _AssertDeactivated()
        elif two_factor_config:
          if not two_factor:
            _AssertReactivated()
          else:
            _AssertNoUpdate()
        else:
          if two_factor:
            _AssertActivated(two_factor=True)
          else:
            _AssertNoUpdate()
      else:
        if oslogin:
          _AssertActivated(two_factor=two_factor)
        else:
          _AssertNoUpdate()
      self.mock_logger.reset_mock()
      self.mock_oslogin.reset_mock()

  def testUpdateOsLoginNotInstalled(self):
    mocks = mock.Mock()
    mocks.attach_mock(self.mock_oslogin, 'oslogin')
    self.mock_oslogin._RunOsLoginControl.return_value = 0
    self.mock_oslogin._GetStatus.return_value = None

    return_value = oslogin_utils.OsLoginUtils.UpdateOsLogin(
        self.mock_oslogin, True)
    expected_calls = [mock.call.oslogin._GetStatus(two_factor=False)]
    self.assertEqual(mocks.mock_calls, expected_calls)
    self.assertEqual(return_value, None)


if __name__ == '__main__':
  unittest.main()
