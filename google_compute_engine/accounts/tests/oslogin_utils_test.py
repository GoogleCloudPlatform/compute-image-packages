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

"""Unittest for accounts_utils.py module."""

from google_compute_engine.accounts import oslogin_utils
from google_compute_engine.test_compat import mock
from google_compute_engine.test_compat import unittest


class AccountsUtilsTest(unittest.TestCase):

  def setUp(self):
    self.mock_logger = mock.Mock()
    self.oslogin_control_script = 'google_oslogin_control'
    #self.groupadd_cmd = 'groupadd {group}'

    self.mock_oslogin = mock.create_autospec(oslogin_utils.OsLoginUtils)
    self.mock_oslogin.logger = self.mock_logger
    self.mock_oslogin.oslogin_installed = True
    #self.mock_utils.groupadd_cmd = self.groupadd_cmd

  def testRunOsLoginControl(self, mock_call):
    mock_logger = mock.Mock()

    oslogin = oslogin_utils.OsLoginUtils(
        logger=mock_logger)
    self.assertEqual(oslogin.logger, mock_logger)

  @mock.patch('google_compute_engine.accounts.oslogin_utils.subprocess.call')
  def testRunOsLoginControl(self, mock_call):
    mocks = mock.Mock()
    mocks.attach_mock(mock_call, 'call')
    mock_call.return_value = 0

    rv = oslogin_utils.OsLoginUtils._RunOsLoginControl(self.mock_oslogin, 'activate')
    expected_calls = [
        mock.call.call([self.oslogin_control_script, 'activate'])
    ]
    self.assertEqual(mocks.mock_calls, expected_calls)
    self.assertEqual(rv, 0)

  @mock.patch('google_compute_engine.accounts.oslogin_utils.subprocess.call')
  def testRunOsLoginControlStatus(self, mock_call):
    mocks = mock.Mock()
    mocks.attach_mock(mock_call, 'call')
    mock_call.return_value = 3

    rv = oslogin_utils.OsLoginUtils._RunOsLoginControl(self.mock_oslogin, 'status')
    expected_calls = [
        mock.call.call([self.oslogin_control_script, 'status'])
    ]
    self.assertEqual(mocks.mock_calls, expected_calls)
    self.assertEqual(rv, 3)

  @mock.patch('google_compute_engine.accounts.oslogin_utils.subprocess.call')
  def testOsLoginNotInstalled(self, mock_call):
    mocks = mock.Mock()
    mocks.attach_mock(mock_call, 'call')
    mock_call.side_effect = OSError(2, 'Not Found')

    rv = oslogin_utils.OsLoginUtils._RunOsLoginControl(self.mock_oslogin, 'status')
    expected_calls = [
        mock.call.call([self.oslogin_control_script, 'status'])
    ]
    self.assertEqual(mocks.mock_calls, expected_calls)
    self.assertEqual(rv, None)

  @mock.patch('google_compute_engine.accounts.oslogin_utils.subprocess.call')
  def testOsLoginControlError(self, mock_call):
    mocks = mock.Mock()
    mocks.attach_mock(mock_call, 'call')
    mock_call.side_effect = OSError

    with self.assertRaises(OSError):
      rv = oslogin_utils.OsLoginUtils._RunOsLoginControl(self.mock_oslogin, 'status')
    expected_calls = [
        mock.call.call([self.oslogin_control_script, 'status'])
    ]
    self.assertEqual(mocks.mock_calls, expected_calls)

  def testGetStatusActive(self):
    mocks = mock.Mock()
    self.mock_oslogin._RunOsLoginControl.return_value = 0
    status = oslogin_utils.OsLoginUtils._GetStatus(self.mock_oslogin)
    self.assertTrue(status)
    expected_calls = []
    self.assertEqual(mocks.mock_calls, expected_calls)

  def testGetStatusNotActive(self):
    mocks = mock.Mock()
    self.mock_oslogin._RunOsLoginControl.return_value = 3
    status = oslogin_utils.OsLoginUtils._GetStatus(self.mock_oslogin)
    self.assertFalse(status)
    expected_calls = []
    self.assertEqual(mocks.mock_calls, expected_calls)

  def testGetStatusNotInstalled(self):
    mocks = mock.Mock()
    self.mock_oslogin._RunOsLoginControl.return_value = None
    mocks.attach_mock(self.mock_logger, 'logger')

    self.assertTrue(self.mock_oslogin.oslogin_installed)
    status1 = oslogin_utils.OsLoginUtils._GetStatus(self.mock_oslogin)
    self.assertFalse(status1)

    self.assertFalse(self.mock_oslogin.oslogin_installed)
    status2 = oslogin_utils.OsLoginUtils._GetStatus(self.mock_oslogin)
    self.assertFalse(status2)

    # Should only log once, even though called twice.
    expected_calls = [
        mock.call.logger.warning(mock.ANY)
    ]
    self.assertEqual(mocks.mock_calls, expected_calls)

  def testUpdateOsLoginActivate(self):
    mocks = mock.Mock()
    mocks.attach_mock(self.mock_logger, 'logger')
    mocks.attach_mock(self.mock_oslogin, 'oslogin')
    self.mock_oslogin._RunOsLoginControl.return_value = 0
    self.mock_oslogin._GetStatus.return_value = False
    status = oslogin_utils.OsLoginUtils.UpdateOsLogin(self.mock_oslogin, True)

    expected_calls = [
        mock.call.oslogin._GetStatus(),
        mock.call.logger.warning(mock.ANY),
        mock.call.oslogin._RunOsLoginControl('activate'),
    ]
    self.assertEqual(mocks.mock_calls, expected_calls)

  def testUpdateOsLoginDeactivate(self):
    mocks = mock.Mock()
    mocks.attach_mock(self.mock_logger, 'logger')
    mocks.attach_mock(self.mock_oslogin, 'oslogin')
    self.mock_oslogin._RunOsLoginControl.return_value = 0
    self.mock_oslogin._GetStatus.return_value = True
    status = oslogin_utils.OsLoginUtils.UpdateOsLogin(self.mock_oslogin, False)

    expected_calls = [
        mock.call.oslogin._GetStatus(),
        mock.call.logger.warning(mock.ANY),
        mock.call.oslogin._RunOsLoginControl('deactivate'),
    ]
    self.assertEqual(mocks.mock_calls, expected_calls)

  def testUpdateOsLoginRedundantActivate(self):
    mocks = mock.Mock()
    mocks.attach_mock(self.mock_oslogin, 'oslogin')
    self.mock_oslogin._RunOsLoginControl.return_value = 0
    self.mock_oslogin._GetStatus.return_value = True
    status = oslogin_utils.OsLoginUtils.UpdateOsLogin(self.mock_oslogin, True)

    expected_calls = [
        mock.call.oslogin._GetStatus(),
    ]
    self.assertEqual(mocks.mock_calls, expected_calls)

  def testUpdateOsLoginRedundantDeactivate(self):
    mocks = mock.Mock()
    mocks.attach_mock(self.mock_oslogin, 'oslogin')
    self.mock_oslogin._RunOsLoginControl.return_value = 0
    self.mock_oslogin._GetStatus.return_value = False
    status = oslogin_utils.OsLoginUtils.UpdateOsLogin(self.mock_oslogin, False)

    expected_calls = [
        mock.call.oslogin._GetStatus(),
    ]
    self.assertEqual(mocks.mock_calls, expected_calls)

  def testUpdateOsLoginNotInstalled(self):
    mocks = mock.Mock()
    mocks.attach_mock(self.mock_oslogin, 'oslogin')
    self.mock_oslogin._RunOsLoginControl.return_value = 0
    self.mock_oslogin._GetStatus.return_value = None
    status = oslogin_utils.OsLoginUtils.UpdateOsLogin(self.mock_oslogin, True)

    expected_calls = [
        mock.call.oslogin._GetStatus(),
    ]
    self.assertEqual(mocks.mock_calls, expected_calls)


if __name__ == '__main__':
  unittest.main()
