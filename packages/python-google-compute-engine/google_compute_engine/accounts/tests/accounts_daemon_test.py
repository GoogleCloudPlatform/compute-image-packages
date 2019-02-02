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

"""Unittest for accounts_daemon.py module."""

import datetime

from google_compute_engine.accounts import accounts_daemon
from google_compute_engine.test_compat import mock
from google_compute_engine.test_compat import unittest


class AccountsDaemonTest(unittest.TestCase):

  def setUp(self):
    self.mock_logger = mock.Mock()
    self.mock_watcher = mock.Mock()
    self.mock_utils = mock.Mock()
    self.mock_oslogin = mock.Mock()

    self.mock_setup = mock.create_autospec(accounts_daemon.AccountsDaemon)
    self.mock_setup.logger = self.mock_logger
    self.mock_setup.watcher = self.mock_watcher
    self.mock_setup.utils = self.mock_utils
    self.mock_setup.oslogin = self.mock_oslogin

  @mock.patch('google_compute_engine.accounts.accounts_daemon.accounts_utils')
  @mock.patch('google_compute_engine.accounts.accounts_daemon.metadata_watcher')
  @mock.patch('google_compute_engine.accounts.accounts_daemon.logger')
  @mock.patch('google_compute_engine.accounts.accounts_daemon.file_utils')
  def testAccountsDaemon(
      self, mock_lock, mock_logger, mock_watcher, mock_utils):
    mock_logger_instance = mock.Mock()
    mock_logger.Logger.return_value = mock_logger_instance
    mocks = mock.Mock()
    mocks.attach_mock(mock_lock, 'lock')
    mocks.attach_mock(mock_logger, 'logger')
    mocks.attach_mock(mock_watcher, 'watcher')
    mocks.attach_mock(mock_utils, 'utils')
    with mock.patch.object(
        accounts_daemon.AccountsDaemon, 'HandleAccounts') as mock_handle:
      accounts_daemon.AccountsDaemon(groups='foo,bar', remove=True, debug=True)
      expected_calls = [
          mock.call.logger.Logger(name=mock.ANY, debug=True, facility=mock.ANY),
          mock.call.watcher.MetadataWatcher(logger=mock_logger_instance),
          mock.call.utils.AccountsUtils(
              logger=mock_logger_instance, groups='foo,bar', remove=True,
              gpasswd_add_cmd=mock.ANY, gpasswd_remove_cmd=mock.ANY,
              groupadd_cmd=mock.ANY, useradd_cmd=mock.ANY,
              userdel_cmd=mock.ANY, usermod_cmd=mock.ANY),
          mock.call.lock.LockFile(accounts_daemon.LOCKFILE),
          mock.call.lock.LockFile().__enter__(),
          mock.call.logger.Logger().info(mock.ANY),
          mock.call.watcher.MetadataWatcher().WatchMetadata(
              mock_handle, recursive=True, timeout=mock.ANY),
          mock.call.lock.LockFile().__exit__(None, None, None),
      ]
      self.assertEqual(mocks.mock_calls, expected_calls)

  @mock.patch('google_compute_engine.accounts.accounts_daemon.accounts_utils')
  @mock.patch('google_compute_engine.accounts.accounts_daemon.metadata_watcher')
  @mock.patch('google_compute_engine.accounts.accounts_daemon.logger')
  @mock.patch('google_compute_engine.accounts.accounts_daemon.file_utils')
  def testAccountsDaemonError(
      self, mock_lock, mock_logger, mock_watcher, mock_utils):
    mock_logger_instance = mock.Mock()
    mock_logger.Logger.return_value = mock_logger_instance
    mocks = mock.Mock()
    mocks.attach_mock(mock_lock, 'lock')
    mocks.attach_mock(mock_logger, 'logger')
    mocks.attach_mock(mock_watcher, 'watcher')
    mocks.attach_mock(mock_utils, 'utils')
    mock_lock.LockFile.side_effect = IOError('Test Error')
    with mock.patch.object(accounts_daemon.AccountsDaemon, 'HandleAccounts'):
      accounts_daemon.AccountsDaemon()
      expected_calls = [
          mock.call.logger.Logger(
              name=mock.ANY, debug=False, facility=mock.ANY),
          mock.call.watcher.MetadataWatcher(logger=mock_logger_instance),
          mock.call.utils.AccountsUtils(
              logger=mock_logger_instance, groups=None, remove=False,
              gpasswd_add_cmd=mock.ANY, gpasswd_remove_cmd=mock.ANY,
              groupadd_cmd=mock.ANY, useradd_cmd=mock.ANY,
              userdel_cmd=mock.ANY, usermod_cmd=mock.ANY),
          mock.call.lock.LockFile(accounts_daemon.LOCKFILE),
          mock.call.logger.Logger().warning('Test Error'),
      ]
      self.assertEqual(mocks.mock_calls, expected_calls)

  def testHasExpired(self):

    def _GetTimestamp(days):
      """Create a timestamp in the correct format with a days offset.

      Args:
        days: int, number of days to add to the current date.

      Returns:
        string, a timestamp with the format '%Y-%m-%dT%H:%M:%S+0000'.
      """
      format_str = '%Y-%m-%dT%H:%M:%S+0000'
      today = datetime.datetime.now()
      timestamp = today + datetime.timedelta(days=days)
      return timestamp.strftime(format_str)

    ssh_keys = {
        None: False,
        '': False,
        'Invalid': False,
        'user:ssh-rsa key user@domain.com': False,
        'user:ssh-rsa key google {"expireOn":"%s"}' % _GetTimestamp(-1): False,
        'user:ssh-rsa key google-ssh': False,
        'user:ssh-rsa key google-ssh {invalid:json}': False,
        'user:ssh-rsa key google-ssh {"userName":"user"}': False,
        'user:ssh-rsa key google-ssh {"expireOn":"invalid"}': False,
        'user:xyz key google-ssh {"expireOn":"%s"}' % _GetTimestamp(1): False,
        'user:xyz key google-ssh {"expireOn":"%s"}' % _GetTimestamp(-1): True,
    }

    for key, expired in ssh_keys.items():
      self.assertEqual(
          accounts_daemon.AccountsDaemon._HasExpired(self.mock_setup, key),
          expired)

  def testParseAccountsData(self):
    user_map = {
        'a': ['1', '2'],
        'b': ['3', '4', '5'],
    }
    accounts_data = 'skip\n'
    for user, keys in user_map.items():
      for key in keys:
        accounts_data += '%s:%s\n' % (user, key)
    # Make the _HasExpired function treat odd numbers as expired SSH keys.
    self.mock_setup._HasExpired.side_effect = lambda key: int(key) % 2 == 0

    self.assertEqual(
        accounts_daemon.AccountsDaemon._ParseAccountsData(
            self.mock_setup, None), {})
    self.assertEqual(
        accounts_daemon.AccountsDaemon._ParseAccountsData(
            self.mock_setup, ''), {})
    expected_users = {'a': ['1'], 'b': ['3', '5']}
    self.assertEqual(accounts_daemon.AccountsDaemon._ParseAccountsData(
        self.mock_setup, accounts_data), expected_users)

  def testParseAccountsDataNonAscii(self):
    accounts_data = [
        'username:rsa ssh-ke%s invalid\n' % chr(165),
        'use%sname:rsa ssh-key\n' % chr(174),
        'username:rsa ssh-key\n',
    ]
    accounts_data = ''.join(accounts_data)
    self.mock_setup._HasExpired.return_value = False
    expected_users = {'username': ['rsa ssh-key']}
    self.assertEqual(accounts_daemon.AccountsDaemon._ParseAccountsData(
        self.mock_setup, accounts_data), expected_users)

  def testGetInstanceAndProjectAttributes(self):

    def _AssertAttributeDict(data, expected):
      """Test the correct accounts data is returned.

      Args:
        data: dictionary, the faux metadata server contents.
        expected: list, the faux SSH keys expected to be set.
      """
      self.assertEqual(
          accounts_daemon.AccountsDaemon._GetInstanceAndProjectAttributes(
              self.mock_setup, data), expected)

    data = None
    _AssertAttributeDict(data, ({}, {}))

    data = {'test': 'data'}
    expected = ({}, {})
    _AssertAttributeDict(data, expected)

    data = {'instance': {'attributes': {}}}
    expected = ({}, {})
    _AssertAttributeDict(data, expected)

    data = {'instance': {'attributes': {'ssh-keys': '1'}}}
    expected = ({'ssh-keys': '1'}, {})
    _AssertAttributeDict(data, expected)

    data = {'instance': {'attributes': {'ssh-keys': '1', 'sshKeys': '2'}}}
    expected = ({'ssh-keys': '1', 'sshKeys': '2'}, {})
    _AssertAttributeDict(data, expected)

    data = {'project': {'attributes': {'ssh-keys': '1'}}}
    expected = ({}, {'ssh-keys': '1'})
    _AssertAttributeDict(data, expected)

    data = {'project': {'attributes': {'ssh-keys': '1', 'sshKeys': '2'}}}
    expected = ({}, {'ssh-keys': '1', 'sshKeys': '2'})
    _AssertAttributeDict(data, expected)

    data = {
        'instance': {
            'attributes': {
                'ssh-keys': '1',
                'sshKeys': '2',
            },
        },
        'project': {
            'attributes': {
                'ssh-keys': '3',
            },
        },
    }
    expected = ({'ssh-keys': '1', 'sshKeys': '2'}, {'ssh-keys': '3'})
    _AssertAttributeDict(data, expected)

    data = {
        'instance': {
            'attributes': {
                'ssh-keys': '1',
                'block-project-ssh-keys': 'false',
            },
        },
        'project': {
            'attributes': {
                'ssh-keys': '2',
            },
        },
    }
    expected = ({'block-project-ssh-keys': 'false', 'ssh-keys': '1'},
                {'ssh-keys': '2'})
    _AssertAttributeDict(data, expected)

    data = {
        'instance': {
            'attributes': {
                'ssh-keys': '1',
                'block-project-ssh-keys': 'true',
            },
        },
        'project': {
            'attributes': {
                'ssh-keys': '2',
            },
        },
    }
    expected = ({'block-project-ssh-keys': 'true', 'ssh-keys': '1'},
                {'ssh-keys': '2'})
    _AssertAttributeDict(data, expected)

    data = {
        'instance': {
            'attributes': {
                'ssh-keys': '1',
                'block-project-ssh-keys': 'false',
            },
        },
        'project': {
            'attributes': {
                'ssh-keys': '2',
                'sshKeys': '3',
            },
        },
    }
    expected = ({'block-project-ssh-keys': 'false', 'ssh-keys': '1'},
                {'sshKeys': '3', 'ssh-keys': '2'})
    _AssertAttributeDict(data, expected)

  def testGetAccountsData(self):

    def _AssertAccountsData(data, expected):
      """Test the correct accounts data is returned.

      Args:
        data: dictionary, the faux metadata server contents.
        expected: list, the faux SSH keys expected to be set.
      """
      self.mock_setup._GetInstanceAndProjectAttributes.return_value = data
      accounts_daemon.AccountsDaemon._GetAccountsData(self.mock_setup, data)
      if expected:
        call_args, _ = self.mock_setup._ParseAccountsData.call_args
        actual = call_args[0]
        self.assertEqual(set(actual.split()), set(expected))
      else:
        self.mock_setup._ParseAccountsData.assert_called_once_with(expected)
      self.mock_setup._ParseAccountsData.reset_mock()

    data = ({}, {})
    _AssertAccountsData(data, '')

    data = ({'ssh-keys': '1'}, {})
    _AssertAccountsData(data, ['1'])

    data = ({'ssh-keys': '1', 'sshKeys': '2'}, {})
    _AssertAccountsData(data, ['1', '2'])

    data = ({}, {'ssh-keys': '1'})
    _AssertAccountsData(data, ['1'])

    data = ({}, {'ssh-keys': '1', 'sshKeys': '2'})
    _AssertAccountsData(data, ['1', '2'])

    data = ({'ssh-keys': '1', 'sshKeys': '2'}, {'ssh-keys': '3'})
    _AssertAccountsData(data, ['1', '2'])

    data = ({'block-project-ssh-keys': 'false', 'ssh-keys': '1'},
            {'ssh-keys': '2'})
    _AssertAccountsData(data, ['1', '2'])

    data = ({'block-project-ssh-keys': 'true', 'ssh-keys': '1'},
            {'ssh-keys': '2'})
    _AssertAccountsData(data, ['1'])

    data = ({'block-project-ssh-keys': 'false', 'ssh-keys': '1'},
            {'sshKeys': '3', 'ssh-keys': '2'})
    _AssertAccountsData(data, ['1', '2', '3'])

  def testGetEnableOsLoginValue(self):

    def _AssertEnableOsLogin(data, expected):
      """Test the correct value for enable-oslogin is returned.

      Args:
        data: dictionary, the faux metadata server contents.
        expected: bool, if True, OS Login is enabled.
      """
      self.mock_setup._GetInstanceAndProjectAttributes.return_value = data
      actual = accounts_daemon.AccountsDaemon._GetEnableOsLoginValue(
          self.mock_setup, data)
      self.assertEqual(actual, expected)

    data = ({}, {})
    _AssertEnableOsLogin(data, False)

    data = ({'enable-oslogin': 'true'}, {})
    _AssertEnableOsLogin(data, True)

    data = ({'enable-oslogin': 'false'}, {})
    _AssertEnableOsLogin(data, False)

    data = ({'enable-oslogin': 'yep'}, {})
    _AssertEnableOsLogin(data, False)

    data = ({'enable-oslogin': 'True'}, {})
    _AssertEnableOsLogin(data, True)

    data = ({'enable-oslogin': 'TRUE'}, {})
    _AssertEnableOsLogin(data, True)

    data = ({'enable-oslogin': ''}, {})
    _AssertEnableOsLogin(data, False)

    data = ({'enable-oslogin': 'true'}, {'enable-oslogin': 'true'})
    _AssertEnableOsLogin(data, True)

    data = ({'enable-oslogin': 'false'}, {'enable-oslogin': 'true'})
    _AssertEnableOsLogin(data, False)

    data = ({'enable-oslogin': ''}, {'enable-oslogin': 'true'})
    _AssertEnableOsLogin(data, True)

    data = ({}, {'enable-oslogin': 'true'})
    _AssertEnableOsLogin(data, True)

    data = ({}, {'enable-oslogin': 'false'})
    _AssertEnableOsLogin(data, False)

    data = ({'block-project-ssh-keys': 'false', 'ssh-keys': '1'},
            {'sshKeys': '3', 'ssh-keys': '2'})
    _AssertEnableOsLogin(data, False)

    data = ({'block-project-ssh-keys': 'false', 'ssh-keys': '1'},
            {'sshKeys': '3', 'ssh-keys': '2', 'enable-oslogin': 'true'})
    _AssertEnableOsLogin(data, True)

  def testGetEnableTwoFactorValue(self):

    def _AssertEnableTwoFactor(data, expected):
      """Test the correct value for enable-oslogin-2fa is returned.

      Args:
        data: dictionary, the faux metadata server contents.
        expected: bool, if True, two factor authentication is enabled.
      """
      self.mock_setup._GetInstanceAndProjectAttributes.return_value = data
      actual = accounts_daemon.AccountsDaemon._GetEnableTwoFactorValue(
          self.mock_setup, data)
      self.assertEqual(actual, expected)

    data = ({}, {})
    _AssertEnableTwoFactor(data, False)

    data = ({'enable-oslogin-2fa': 'true'}, {})
    _AssertEnableTwoFactor(data, True)

    data = ({'enable-oslogin-2fa': 'false'}, {})
    _AssertEnableTwoFactor(data, False)

    data = ({'enable-oslogin-2fa': 'yep'}, {})
    _AssertEnableTwoFactor(data, False)

    data = ({'enable-oslogin-2fa': 'True'}, {})
    _AssertEnableTwoFactor(data, True)

    data = ({'enable-oslogin-2fa': 'TRUE'}, {})
    _AssertEnableTwoFactor(data, True)

    data = ({'enable-oslogin-2fa': ''}, {})
    _AssertEnableTwoFactor(data, False)

    data = ({'enable-oslogin-2fa': 'true'}, {'enable-oslogin-2fa': 'true'})
    _AssertEnableTwoFactor(data, True)

    data = ({'enable-oslogin-2fa': 'false'}, {'enable-oslogin-2fa': 'true'})
    _AssertEnableTwoFactor(data, False)

    data = ({'enable-oslogin-2fa': ''}, {'enable-oslogin-2fa': 'true'})
    _AssertEnableTwoFactor(data, True)

    data = ({}, {'enable-oslogin-2fa': 'true'})
    _AssertEnableTwoFactor(data, True)

    data = ({}, {'enable-oslogin-2fa': 'false'})
    _AssertEnableTwoFactor(data, False)

    data = ({'block-project-ssh-keys': 'false', 'ssh-keys': '1'},
            {'sshKeys': '3', 'ssh-keys': '2'})
    _AssertEnableTwoFactor(data, False)

    data = ({'block-project-ssh-keys': 'false', 'ssh-keys': '1'},
            {'sshKeys': '3', 'ssh-keys': '2', 'enable-oslogin-2fa': 'true'})
    _AssertEnableTwoFactor(data, True)

  def testUpdateUsers(self):
    update_users = {
        'a': '1',
        'b': '2',
        'c': '3',
        'invalid': '4',
        'valid': '5',
        'unchanged': ['1', '2', '3'],
    }
    self.mock_setup.user_ssh_keys = {
        'unchanged': ['3', '2', '1'],
    }
    self.mock_setup.invalid_users = set(['invalid'])
    # Make UpdateUser succeed for fake names longer than one character.
    self.mock_utils.UpdateUser.side_effect = lambda user, _: len(user) > 1
    accounts_daemon.AccountsDaemon._UpdateUsers(self.mock_setup, update_users)
    expected_calls = [
        mock.call('a', '1'),
        mock.call('b', '2'),
        mock.call('c', '3'),
        mock.call('valid', '5'),
    ]
    self.mock_utils.UpdateUser.assert_has_calls(expected_calls, any_order=True)
    self.assertEqual(
        self.mock_utils.UpdateUser.call_count, len(expected_calls))
    self.assertEqual(
        self.mock_setup.invalid_users, set(['invalid', 'a', 'b', 'c']))
    self.assertEqual(
        self.mock_setup.user_ssh_keys,
        {'valid': '5', 'unchanged': ['3', '2', '1']})

  def testRemoveUsers(self):
    remove_users = ['a', 'b', 'c', 'valid']
    self.mock_setup.user_ssh_keys = {
        'a': ['1'],
        'b': ['2'],
        'c': ['3'],
        'invalid': ['key'],
    }
    self.mock_setup.invalid_users = set(['invalid', 'a', 'b', 'c'])
    accounts_daemon.AccountsDaemon._RemoveUsers(self.mock_setup, remove_users)
    expected_calls = [
        mock.call('a'),
        mock.call('b'),
        mock.call('c'),
        mock.call('valid'),
    ]
    self.mock_utils.RemoveUser.assert_has_calls(expected_calls)
    self.assertEqual(self.mock_setup.invalid_users, set(['invalid']))
    self.assertEqual(self.mock_setup.user_ssh_keys, {'invalid': ['key']})

  def testHandleAccountsNoOsLogin(self):
    configured = ['c', 'c', 'b', 'b', 'a', 'a']
    desired = {'d': '1', 'c': '2'}
    mocks = mock.Mock()
    mocks.attach_mock(self.mock_utils, 'utils')
    mocks.attach_mock(self.mock_setup, 'setup')
    mocks.attach_mock(self.mock_oslogin, 'oslogin')
    self.mock_utils.GetConfiguredUsers.return_value = configured
    self.mock_setup._GetAccountsData.return_value = desired
    self.mock_setup._GetEnableOsLoginValue.return_value = False
    self.mock_oslogin.UpdateOsLogin.return_value = 0
    result = 'result'
    expected_add = ['c', 'd']
    expected_remove = ['a', 'b']

    accounts_daemon.AccountsDaemon.HandleAccounts(self.mock_setup, result)
    expected_calls = [
        mock.call.setup.logger.debug(mock.ANY),
        mock.call.utils.GetConfiguredUsers(),
        mock.call.setup._GetEnableOsLoginValue(result),
        mock.call.setup._GetEnableTwoFactorValue(result),
        mock.call.setup._GetAccountsData(result),
        mock.call.oslogin.UpdateOsLogin(False),
        mock.call.setup._UpdateUsers(desired),
        mock.call.setup._RemoveUsers(mock.ANY),
        mock.call.utils.SetConfiguredUsers(mock.ANY),
    ]
    self.assertEqual(mocks.mock_calls, expected_calls)
    call_args, _ = self.mock_utils.SetConfiguredUsers.call_args
    self.assertEqual(set(call_args[0]), set(expected_add))
    call_args, _ = self.mock_setup._RemoveUsers.call_args
    self.assertEqual(set(call_args[0]), set(expected_remove))

  def testHandleAccountsOsLogin(self):
    configured = ['c', 'c', 'b', 'b', 'a', 'a']
    desired = {}
    mocks = mock.Mock()
    mocks.attach_mock(self.mock_utils, 'utils')
    mocks.attach_mock(self.mock_setup, 'setup')
    mocks.attach_mock(self.mock_oslogin, 'oslogin')
    self.mock_utils.GetConfiguredUsers.return_value = configured
    self.mock_setup._GetAccountsData.return_value = desired
    self.mock_setup._GetEnableOsLoginValue.return_value = True
    self.mock_setup._GetEnableTwoFactorValue.return_value = False
    self.mock_oslogin.UpdateOsLogin.return_value = 0
    result = 'result'
    expected_add = []
    expected_remove = ['a', 'b', 'c']

    accounts_daemon.AccountsDaemon.HandleAccounts(self.mock_setup, result)
    expected_calls = [
        mock.call.setup.logger.debug(mock.ANY),
        mock.call.utils.GetConfiguredUsers(),
        mock.call.setup._GetEnableOsLoginValue(result),
        mock.call.setup._GetEnableTwoFactorValue(result),
        mock.call.oslogin.UpdateOsLogin(True, two_factor_desired=False),
        mock.call.setup._UpdateUsers(desired),
        mock.call.setup._RemoveUsers(mock.ANY),
        mock.call.utils.SetConfiguredUsers(mock.ANY),
    ]
    self.assertEqual(mocks.mock_calls, expected_calls)
    call_args, _ = self.mock_utils.SetConfiguredUsers.call_args
    self.assertEqual(set(call_args[0]), set(expected_add))
    call_args, _ = self.mock_setup._RemoveUsers.call_args
    self.assertEqual(set(call_args[0]), set(expected_remove))


if __name__ == '__main__':
  unittest.main()
