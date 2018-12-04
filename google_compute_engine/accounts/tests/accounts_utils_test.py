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

"""Unittest for accounts_utils.py module."""

import subprocess

from google_compute_engine.accounts import accounts_utils
from google_compute_engine.test_compat import builtin
from google_compute_engine.test_compat import mock
from google_compute_engine.test_compat import unittest


class AccountsUtilsTest(unittest.TestCase):

  def setUp(self):
    self.mock_logger = mock.Mock()
    self.sudoers_group = 'google-sudoers'
    self.sudoers_file = '/sudoers/file'
    self.users_dir = '/users'
    self.users_file = '/users/file'
    self.gpasswd_add_cmd = 'gpasswd -a {user} {group}'
    self.gpasswd_remove_cmd = 'gpasswd -d {user} {group}'
    self.groupadd_cmd = 'groupadd {group}'
    self.useradd_cmd = 'useradd -m -s /bin/bash -p * {user}'
    self.userdel_cmd = 'userdel -r {user}'
    self.usermod_cmd = 'usermod -G {groups} {user}'

    self.mock_utils = mock.create_autospec(accounts_utils.AccountsUtils)
    self.mock_utils.google_comment = accounts_utils.AccountsUtils.google_comment
    self.mock_utils.google_sudoers_group = self.sudoers_group
    self.mock_utils.google_sudoers_file = self.sudoers_file
    self.mock_utils.google_users_dir = self.users_dir
    self.mock_utils.google_users_file = self.users_file
    self.mock_utils.logger = self.mock_logger
    self.mock_utils.gpasswd_add_cmd = self.gpasswd_add_cmd
    self.mock_utils.gpasswd_remove_cmd = self.gpasswd_remove_cmd
    self.mock_utils.groupadd_cmd = self.groupadd_cmd
    self.mock_utils.useradd_cmd = self.useradd_cmd
    self.mock_utils.userdel_cmd = self.userdel_cmd
    self.mock_utils.usermod_cmd = self.usermod_cmd

  @mock.patch('google_compute_engine.accounts.accounts_utils.AccountsUtils._GetGroup')
  @mock.patch('google_compute_engine.accounts.accounts_utils.AccountsUtils._CreateSudoersGroup')
  def testAccountsUtils(self, mock_create, mock_group):
    mock_logger = mock.Mock()
    mock_group.side_effect = lambda group: 'google' in group

    utils = accounts_utils.AccountsUtils(
        logger=mock_logger, groups='foo,google,bar', remove=True)
    mock_create.assert_called_once_with()
    self.assertEqual(utils.logger, mock_logger)
    self.assertEqual(sorted(utils.groups), ['google'])
    self.assertTrue(utils.remove)

  @mock.patch('google_compute_engine.accounts.accounts_utils.grp')
  def testGetGroup(self, mock_grp):
    mock_grp.getgrnam.return_value = 'Test'
    self.assertEqual(
        accounts_utils.AccountsUtils._GetGroup(self.mock_utils, 'valid'),
        'Test')
    mock_grp.getgrnam.side_effect = KeyError('Test Error')
    self.assertEqual(
        accounts_utils.AccountsUtils._GetGroup(self.mock_utils, 'invalid'),
        None)
    expected_calls = [
        mock.call.getgrnam('valid'),
        mock.call.getgrnam('invalid'),
    ]
    self.assertEqual(mock_grp.mock_calls, expected_calls)

  @mock.patch('google_compute_engine.accounts.accounts_utils.file_utils.SetPermissions')
  @mock.patch('google_compute_engine.accounts.accounts_utils.subprocess.check_call')
  @mock.patch('google_compute_engine.accounts.accounts_utils.os.path.exists')
  def testCreateSudoersGroup(self, mock_exists, mock_call, mock_permissions):
    mock_open = mock.mock_open()
    mocks = mock.Mock()
    mocks.attach_mock(mock_exists, 'exists')
    mocks.attach_mock(mock_call, 'call')
    mocks.attach_mock(mock_permissions, 'permissions')
    mocks.attach_mock(self.mock_utils._GetGroup, 'group')
    mocks.attach_mock(self.mock_logger, 'logger')
    self.mock_utils._GetGroup.return_value = False
    mock_exists.return_value = False
    command = self.groupadd_cmd.format(group=self.sudoers_group)

    with mock.patch('%s.open' % builtin, mock_open, create=False):
      accounts_utils.AccountsUtils._CreateSudoersGroup(self.mock_utils)
      mock_open().write.assert_called_once_with(mock.ANY)

    expected_calls = [
        mock.call.group(self.sudoers_group),
        mock.call.call(command.split(' ')),
        mock.call.exists(self.sudoers_file),
        mock.call.permissions(self.sudoers_file, mode=0o440, uid=0, gid=0),
    ]
    self.assertEqual(mocks.mock_calls, expected_calls)

  @mock.patch('google_compute_engine.accounts.accounts_utils.file_utils.SetPermissions')
  @mock.patch('google_compute_engine.accounts.accounts_utils.subprocess.check_call')
  @mock.patch('google_compute_engine.accounts.accounts_utils.os.path.exists')
  def testCreateSudoersGroupSkip(
      self, mock_exists, mock_call, mock_permissions):
    mock_open = mock.mock_open()
    mocks = mock.Mock()
    mocks.attach_mock(mock_exists, 'exists')
    mocks.attach_mock(mock_call, 'call')
    mocks.attach_mock(mock_permissions, 'permissions')
    mocks.attach_mock(self.mock_utils._GetGroup, 'group')
    mocks.attach_mock(self.mock_logger, 'logger')
    self.mock_utils._GetGroup.return_value = True
    mock_exists.return_value = True

    with mock.patch('%s.open' % builtin, mock_open, create=False):
      accounts_utils.AccountsUtils._CreateSudoersGroup(self.mock_utils)
      mock_open().write.assert_not_called()

    expected_calls = [
        mock.call.group(self.sudoers_group),
        mock.call.exists(self.sudoers_file),
        mock.call.permissions(self.sudoers_file, mode=0o440, uid=0, gid=0),
    ]
    self.assertEqual(mocks.mock_calls, expected_calls)

  @mock.patch('google_compute_engine.accounts.accounts_utils.file_utils.SetPermissions')
  @mock.patch('google_compute_engine.accounts.accounts_utils.subprocess.check_call')
  @mock.patch('google_compute_engine.accounts.accounts_utils.os.path.exists')
  def testCreateSudoersGroupError(
      self, mock_exists, mock_call, mock_permissions):
    mocks = mock.Mock()
    mocks.attach_mock(mock_exists, 'exists')
    mocks.attach_mock(mock_call, 'call')
    mocks.attach_mock(mock_permissions, 'permissions')
    mocks.attach_mock(self.mock_utils._GetGroup, 'group')
    mocks.attach_mock(self.mock_logger, 'logger')
    self.mock_utils._GetGroup.return_value = False
    mock_exists.return_value = True
    mock_call.side_effect = subprocess.CalledProcessError(1, 'Test')
    command = self.groupadd_cmd.format(group=self.sudoers_group)

    accounts_utils.AccountsUtils._CreateSudoersGroup(self.mock_utils)
    expected_calls = [
        mock.call.group(self.sudoers_group),
        mock.call.call(command.split(' ')),
        mock.call.logger.warning(mock.ANY, mock.ANY),
        mock.call.exists(self.sudoers_file),
        mock.call.permissions(self.sudoers_file, mode=0o440, uid=0, gid=0),
    ]
    self.assertEqual(mocks.mock_calls, expected_calls)

  @mock.patch('google_compute_engine.accounts.accounts_utils.os.path.exists')
  def testCreateSudoersGroupWriteError(self, mock_exists):
    mock_open = mock.mock_open()
    mocks = mock.Mock()
    mocks.attach_mock(mock_exists, 'exists')
    mocks.attach_mock(self.mock_utils._GetGroup, 'group')
    mocks.attach_mock(self.mock_logger, 'logger')
    self.mock_utils._GetGroup.return_value = True
    mock_exists.return_value = False
    mock_open.side_effect = IOError()

    accounts_utils.AccountsUtils._CreateSudoersGroup(self.mock_utils)
    expected_calls = [
        mock.call.group(self.sudoers_group),
        mock.call.exists(self.sudoers_file),
        mock.call.logger.error(mock.ANY, self.sudoers_file, mock.ANY),
    ]
    self.assertEqual(mocks.mock_calls, expected_calls)

  @mock.patch('google_compute_engine.accounts.accounts_utils.pwd')
  def testGetUser(self, mock_pwd):
    mock_pwd.getpwnam.return_value = 'Test'
    self.assertEqual(
        accounts_utils.AccountsUtils._GetUser(self.mock_utils, 'valid'),
        'Test')
    mock_pwd.getpwnam.side_effect = KeyError('Test Error')
    self.assertEqual(
        accounts_utils.AccountsUtils._GetUser(self.mock_utils, 'invalid'),
        None)
    expected_calls = [
        mock.call.getpwnam('valid'),
        mock.call.getpwnam('invalid'),
    ]
    self.assertEqual(mock_pwd.mock_calls, expected_calls)

  @mock.patch('google_compute_engine.accounts.accounts_utils.subprocess.check_call')
  def testAddUser(self, mock_call):
    user = 'user'
    command = self.useradd_cmd.format(user=user)

    self.assertTrue(
        accounts_utils.AccountsUtils._AddUser(self.mock_utils, user))
    mock.call.assert_called_once_with(command.split(' ')),
    expected_calls = [mock.call.info(mock.ANY, user)] * 2
    self.assertEqual(self.mock_logger.mock_calls, expected_calls)

  @mock.patch('google_compute_engine.accounts.accounts_utils.subprocess.check_call')
  def testAddUserError(self, mock_call):
    user = 'user'
    command = self.useradd_cmd.format(user=user)
    mock_call.side_effect = subprocess.CalledProcessError(1, 'Test')

    self.assertFalse(
        accounts_utils.AccountsUtils._AddUser(self.mock_utils, user))
    mock.call.assert_called_once_with(command.split(' ')),
    expected_calls = [
        mock.call.info(mock.ANY, user),
        mock.call.warning(mock.ANY, user, mock.ANY),
    ]
    self.assertEqual(self.mock_logger.mock_calls, expected_calls)

  @mock.patch('google_compute_engine.accounts.accounts_utils.subprocess.check_call')
  def testUpdateUserGroups(self, mock_call):
    user = 'user'
    groups = ['a', 'b', 'c']
    groups_string = ','.join(groups)
    command = self.usermod_cmd.format(user=user, groups=groups_string)

    self.assertTrue(
        accounts_utils.AccountsUtils._UpdateUserGroups(
            self.mock_utils, user, groups))
    mock.call.assert_called_once_with(command.split(' ')),
    expected_calls = [
        mock.call.debug(mock.ANY, user, groups_string),
        mock.call.debug(mock.ANY, user),
    ]
    self.assertEqual(self.mock_logger.mock_calls, expected_calls)

  @mock.patch('google_compute_engine.accounts.accounts_utils.subprocess.check_call')
  def testUpdateUserGroupsError(self, mock_call):
    user = 'user'
    groups = ['a', 'b', 'c']
    groups_string = ','.join(groups)
    command = self.usermod_cmd.format(user=user, groups=groups_string)
    mock_call.side_effect = subprocess.CalledProcessError(1, 'Test')

    self.assertFalse(
        accounts_utils.AccountsUtils._UpdateUserGroups(
            self.mock_utils, user, groups))
    mock.call.assert_called_once_with(command.split(' ')),
    expected_calls = [
        mock.call.debug(mock.ANY, user, groups_string),
        mock.call.warning(mock.ANY, user, mock.ANY),
    ]
    self.assertEqual(self.mock_logger.mock_calls, expected_calls)

  @mock.patch('google_compute_engine.accounts.accounts_utils.file_utils.SetPermissions')
  @mock.patch('google_compute_engine.accounts.accounts_utils.shutil.copy')
  @mock.patch('google_compute_engine.accounts.accounts_utils.tempfile.NamedTemporaryFile')
  @mock.patch('google_compute_engine.accounts.accounts_utils.os.path.exists')
  @mock.patch('google_compute_engine.accounts.accounts_utils.os.path.islink')
  def testUpdateAuthorizedKeys(
      self, mock_islink, mock_exists, mock_tempfile, mock_copy,
      mock_permissions):
    mock_open = mock.mock_open()
    user = 'user'
    ssh_keys = ['Google key 1', 'Google key 2']
    temp_dest = '/tmp/dest'
    pw_uid = 1
    pw_gid = 2
    pw_dir = '/home'
    ssh_dir = '/home/.ssh'
    authorized_keys_file = '/home/.ssh/authorized_keys'
    pw_entry = accounts_utils.pwd.struct_passwd(
        ('', '', pw_uid, pw_gid, '', pw_dir, ''))
    self.mock_utils._GetUser.return_value = pw_entry
    mock_islink.return_value = False
    mock_exists.return_value = True
    mock_tempfile.return_value = mock_tempfile
    mock_tempfile.__enter__.return_value.name = temp_dest
    self.mock_logger.name = 'test'

    with mock.patch('%s.open' % builtin, mock_open, create=False):
      mock_open().readlines.return_value = [
          'User key a\n',
          'User key b\n',
          '\n',
          self.mock_utils.google_comment + '\n',
          'Google key a\n',
          self.mock_utils.google_comment + '\n',
          'Google key b\n',
          'User key c\n',
      ]
      accounts_utils.AccountsUtils._UpdateAuthorizedKeys(
          self.mock_utils, user, ssh_keys)

    expected_calls = [
        mock.call(mode='w', prefix='test-', delete=True),
        mock.call.__enter__(),
        mock.call.__enter__().write('User key a\n'),
        mock.call.__enter__().write('User key b\n'),
        mock.call.__enter__().write('\n'),
        mock.call.__enter__().write('User key c\n'),
        mock.call.__enter__().write(self.mock_utils.google_comment + '\n'),
        mock.call.__enter__().write('Google key 1\n'),
        mock.call.__enter__().write(self.mock_utils.google_comment + '\n'),
        mock.call.__enter__().write('Google key 2\n'),
        mock.call.__enter__().flush(),
        mock.call.__exit__(None, None, None),
    ]
    self.assertEqual(mock_tempfile.mock_calls, expected_calls)
    mock_copy.assert_called_once_with(temp_dest, authorized_keys_file)
    expected_calls = [
        mock.call(ssh_dir, mode=0o700, uid=pw_uid, gid=pw_gid, mkdir=True),
        mock.call(authorized_keys_file, mode=0o600, uid=pw_uid, gid=pw_gid),
    ]
    self.assertEqual(mock_permissions.mock_calls, expected_calls)
    self.mock_logger.warning.assert_not_called()

  @mock.patch('google_compute_engine.accounts.accounts_utils.file_utils.SetPermissions')
  @mock.patch('google_compute_engine.accounts.accounts_utils.shutil.copy')
  @mock.patch('google_compute_engine.accounts.accounts_utils.tempfile.NamedTemporaryFile')
  @mock.patch('google_compute_engine.accounts.accounts_utils.os.path.exists')
  @mock.patch('google_compute_engine.accounts.accounts_utils.os.path.islink')
  def testUpdateAuthorizedKeysNoKeys(
      self, mock_islink, mock_exists, mock_tempfile, mock_copy,
      mock_permissions):
    user = 'user'
    ssh_keys = ['Google key 1']
    temp_dest = '/tmp/dest'
    pw_uid = 1
    pw_gid = 2
    pw_dir = '/home'
    ssh_dir = '/home/.ssh'
    authorized_keys_file = '/home/.ssh/authorized_keys'
    pw_entry = accounts_utils.pwd.struct_passwd(
        ('', '', pw_uid, pw_gid, '', pw_dir, ''))
    self.mock_utils._GetUser.return_value = pw_entry
    mock_islink.return_value = False
    mock_exists.side_effect = [True, False]
    mock_tempfile.return_value = mock_tempfile
    mock_tempfile.__enter__.return_value.name = temp_dest
    self.mock_logger.name = 'test'

    # The authorized keys file does not exist so write a new one.
    accounts_utils.AccountsUtils._UpdateAuthorizedKeys(
        self.mock_utils, user, ssh_keys)
    expected_calls = [
        mock.call(mode='w', prefix='test-', delete=True),
        mock.call.__enter__(),
        mock.call.__enter__().write(self.mock_utils.google_comment + '\n'),
        mock.call.__enter__().write('Google key 1\n'),
        mock.call.__enter__().flush(),
        mock.call.__exit__(None, None, None),
    ]
    self.assertEqual(mock_tempfile.mock_calls, expected_calls)
    mock_copy.assert_called_once_with(temp_dest, authorized_keys_file)
    expected_calls = [
        mock.call(ssh_dir, mode=0o700, uid=pw_uid, gid=pw_gid, mkdir=True),
        mock.call(authorized_keys_file, mode=0o600, uid=pw_uid, gid=pw_gid),
    ]
    self.assertEqual(mock_permissions.mock_calls, expected_calls)
    self.mock_logger.warning.assert_not_called()

  @mock.patch('google_compute_engine.accounts.accounts_utils.file_utils.SetPermissions')
  @mock.patch('google_compute_engine.accounts.accounts_utils.shutil.copy')
  @mock.patch('google_compute_engine.accounts.accounts_utils.tempfile.NamedTemporaryFile')
  @mock.patch('google_compute_engine.accounts.accounts_utils.os.path.exists')
  @mock.patch('google_compute_engine.accounts.accounts_utils.os.path.islink')
  def testUpdateAuthorizedKeysNoHomeDir(
      self, mock_islink, mock_exists, mock_tempfile, mock_copy,
      mock_permissions):
    user = 'user'
    ssh_keys = ['Google key 1']
    temp_dest = '/tmp/dest'
    pw_uid = 1
    pw_gid = 2
    pw_dir = '/home/user'
    ssh_dir = '/home/user/.ssh'
    authorized_keys_file = '/home/user/.ssh/authorized_keys'
    pw_entry = accounts_utils.pwd.struct_passwd(
        ('', '', pw_uid, pw_gid, '', pw_dir, ''))
    self.mock_utils._GetUser.return_value = pw_entry
    mock_islink.return_value = False
    mock_exists.side_effect = [False, False]
    mock_tempfile.return_value = mock_tempfile
    mock_tempfile.__enter__.return_value.name = temp_dest
    self.mock_logger.name = 'test'
    accounts_utils.AccountsUtils._UpdateAuthorizedKeys(
        self.mock_utils, user, ssh_keys)
    expected_calls = [
        mock.call(pw_dir, mode=0o755, uid=pw_uid, gid=pw_gid, mkdir=True),
        mock.call(ssh_dir, mode=0o700, uid=pw_uid, gid=pw_gid, mkdir=True),
        mock.call(authorized_keys_file, mode=0o600, uid=pw_uid, gid=pw_gid),
    ]
    self.assertEqual(mock_permissions.mock_calls, expected_calls)

  @mock.patch('google_compute_engine.accounts.accounts_utils.file_utils.SetPermissions')
  def testUpdateAuthorizedKeysNoUser(self, mock_permissions):
    user = 'user'
    ssh_keys = ['key']
    self.mock_utils._GetUser.return_value = None

    # The user does not exist, so do not write authorized keys.
    accounts_utils.AccountsUtils._UpdateAuthorizedKeys(
        self.mock_utils, user, ssh_keys)
    self.mock_utils._GetUser.assert_called_once_with(user)
    mock_permissions.assert_not_called()
    self.mock_logger.warning.assert_not_called()

  @mock.patch('google_compute_engine.accounts.accounts_utils.file_utils.SetPermissions')
  @mock.patch('google_compute_engine.accounts.accounts_utils.os.path.islink')
  def testUpdateAuthorizedKeysSymlink(self, mock_islink, mock_permissions):
    user = 'user'
    ssh_keys = ['Google key 1']
    pw_uid = 1
    pw_gid = 2
    pw_dir = '/home'
    ssh_dir = '/home/.ssh'
    authorized_keys_file = '/home/.ssh/authorized_keys'
    pw_entry = accounts_utils.pwd.struct_passwd(
        ('', '', pw_uid, pw_gid, '', pw_dir, ''))
    self.mock_utils._GetUser.return_value = pw_entry
    mock_islink.side_effect = [False, True]

    accounts_utils.AccountsUtils._UpdateAuthorizedKeys(
        self.mock_utils, user, ssh_keys)
    expected_calls = [mock.call(ssh_dir), mock.call(authorized_keys_file)]
    self.assertEqual(mock_islink.mock_calls, expected_calls)
    self.mock_logger.warning.assert_called_once_with(mock.ANY, user)
    mock_permissions.assert_not_called()

  @mock.patch('google_compute_engine.accounts.accounts_utils.subprocess.check_call')
  def testUpdateSudoer(self, mock_call):
    user = 'user'
    command = self.gpasswd_remove_cmd.format(
        user=user, group=self.sudoers_group)

    self.assertTrue(
        accounts_utils.AccountsUtils._UpdateSudoer(self.mock_utils, user))
    mock.call.assert_called_once_with(command.split(' '))
    expected_calls = [
        mock.call.info(mock.ANY, user),
        mock.call.debug(mock.ANY, user),
    ]
    self.assertEqual(self.mock_logger.mock_calls, expected_calls)

  @mock.patch('google_compute_engine.accounts.accounts_utils.subprocess.check_call')
  def testUpdateSudoerAddSudoer(self, mock_call):
    user = 'user'
    command = self.gpasswd_add_cmd.format(user=user, group=self.sudoers_group)

    self.assertTrue(
        accounts_utils.AccountsUtils._UpdateSudoer(
            self.mock_utils, user, sudoer=True))
    mock.call.assert_called_once_with(command.split(' '))
    expected_calls = [
        mock.call.info(mock.ANY, user),
        mock.call.debug(mock.ANY, user),
    ]
    self.assertEqual(self.mock_logger.mock_calls, expected_calls)

  @mock.patch('google_compute_engine.accounts.accounts_utils.subprocess.check_call')
  def testUpdateSudoerError(self, mock_call):
    user = 'user'
    command = self.usermod_cmd.format(user=user, groups=self.sudoers_group)
    mock_call.side_effect = subprocess.CalledProcessError(1, 'Test')

    self.assertFalse(
        accounts_utils.AccountsUtils._UpdateSudoer(self.mock_utils, user))
    mock.call.assert_called_once_with(command.split(' '))
    expected_calls = [
        mock.call.info(mock.ANY, user),
        mock.call.warning(mock.ANY, user, mock.ANY),
    ]
    self.assertEqual(self.mock_logger.mock_calls, expected_calls)

  @mock.patch('google_compute_engine.accounts.accounts_utils.os.remove')
  @mock.patch('google_compute_engine.accounts.accounts_utils.os.path.exists')
  def testRemoveAuthorizedKeys(self, mock_exists, mock_remove):
    user = 'user'
    pw_dir = '/home'
    authorized_keys_file = '/home/.ssh/authorized_keys'
    pw_entry = accounts_utils.pwd.struct_passwd(
        ('', '', '', '', '', pw_dir, ''))
    self.mock_utils._GetUser.return_value = pw_entry
    mock_exists.return_value = True

    accounts_utils.AccountsUtils._RemoveAuthorizedKeys(self.mock_utils, user)
    self.mock_utils._GetUser.assert_called_once_with(user)
    mock_exists.assert_called_once_with(authorized_keys_file)
    mock_remove.assert_called_once_with(authorized_keys_file)
    self.mock_logger.warning.assert_not_called()

  @mock.patch('google_compute_engine.accounts.accounts_utils.os.remove')
  @mock.patch('google_compute_engine.accounts.accounts_utils.os.path.exists')
  def testRemoveAuthorizedKeysNoKeys(self, mock_exists, mock_remove):
    user = 'user'
    pw_dir = '/home'
    authorized_keys_file = '/home/.ssh/authorized_keys'
    pw_entry = accounts_utils.pwd.struct_passwd(
        ('', '', '', '', '', pw_dir, ''))
    self.mock_utils._GetUser.return_value = pw_entry
    mock_exists.return_value = False

    accounts_utils.AccountsUtils._RemoveAuthorizedKeys(self.mock_utils, user)
    self.mock_utils._GetUser.assert_called_once_with(user)
    mock_exists.assert_called_once_with(authorized_keys_file)
    mock_remove.assert_not_called()

  @mock.patch('google_compute_engine.accounts.accounts_utils.os.path.exists')
  def testRemoveAuthorizedKeysNoUser(self, mock_exists):
    user = 'user'
    self.mock_utils._GetUser.return_value = None

    accounts_utils.AccountsUtils._RemoveAuthorizedKeys(self.mock_utils, user)
    self.mock_utils._GetUser.assert_called_once_with(user)
    mock_exists.assert_not_called()

  @mock.patch('google_compute_engine.accounts.accounts_utils.os.remove')
  @mock.patch('google_compute_engine.accounts.accounts_utils.os.path.exists')
  def testRemoveAuthorizedKeysError(self, mock_exists, mock_remove):
    user = 'user'
    pw_dir = '/home'
    authorized_keys_file = '/home/.ssh/authorized_keys'
    pw_entry = accounts_utils.pwd.struct_passwd(
        ('', '', '', '', '', pw_dir, ''))
    self.mock_utils._GetUser.return_value = pw_entry
    mock_exists.return_value = True
    mock_remove.side_effect = OSError('Test Error')

    accounts_utils.AccountsUtils._RemoveAuthorizedKeys(self.mock_utils, user)
    self.mock_utils._GetUser.assert_called_once_with(user)
    mock_exists.assert_called_once_with(authorized_keys_file)
    mock_remove.assert_called_once_with(authorized_keys_file)
    self.mock_logger.warning.assert_called_once_with(mock.ANY, user, mock.ANY)

  @mock.patch('google_compute_engine.accounts.accounts_utils.os.path.exists')
  def testGetConfiguredUsers(self, mock_exists):
    mock_open = mock.mock_open()
    mock_exists.return_value = True
    with mock.patch('%s.open' % builtin, mock_open, create=False):
      mock_open().readlines.return_value = ['a\n', 'b\n', 'c\n', '\n']
      self.assertEqual(
          accounts_utils.AccountsUtils.GetConfiguredUsers(self.mock_utils),
          ['a', 'b', 'c', ''])

  @mock.patch('google_compute_engine.accounts.accounts_utils.os.path.exists')
  def testGetConfiguredUsersEmpty(self, mock_exists):
    mock_exists.return_value = False
    self.assertEqual(
        accounts_utils.AccountsUtils.GetConfiguredUsers(self.mock_utils), [])

  @mock.patch('google_compute_engine.accounts.accounts_utils.os.makedirs')
  @mock.patch('google_compute_engine.accounts.accounts_utils.os.path.exists')
  @mock.patch('google_compute_engine.accounts.accounts_utils.file_utils.SetPermissions')
  @mock.patch('google_compute_engine.accounts.accounts_utils.shutil.copy')
  @mock.patch('google_compute_engine.accounts.accounts_utils.tempfile.NamedTemporaryFile')
  def testSetConfiguredUsers(
      self, mock_tempfile, mock_copy, mock_permissions, mock_exists,
      mock_makedirs):
    temp_dest = '/temp/dest'
    users = ['a', 'b', 'c']
    mock_tempfile.return_value = mock_tempfile
    mock_tempfile.__enter__.return_value.name = temp_dest
    mock_exists.return_value = False
    self.mock_logger.name = 'test'

    accounts_utils.AccountsUtils.SetConfiguredUsers(self.mock_utils, users)

    expected_calls = [
        mock.call(mode='w', prefix='test-', delete=True),
        mock.call.__enter__(),
        mock.call.__enter__().write('a\n'),
        mock.call.__enter__().write('b\n'),
        mock.call.__enter__().write('c\n'),
        mock.call.__enter__().flush(),
        mock.call.__exit__(None, None, None),
    ]
    self.assertEqual(mock_tempfile.mock_calls, expected_calls)
    mock_makedirs.assert_called_once_with(self.users_dir)
    mock_copy.assert_called_once_with(temp_dest, self.users_file)
    mock_permissions.assert_called_once_with(
        self.users_file, mode=0o600, uid=0, gid=0)

  def testUpdateUser(self):
    valid_users = [
        'user',
        '_',
        '.',
        '.abc_',
        '_abc-',
        'ABC',
        'A_.-',
    ]
    groups = ['a', 'b', 'c']
    keys = ['Key 1', 'Key 2']
    pw_entry = accounts_utils.pwd.struct_passwd(tuple(['']*7))
    self.mock_utils.groups = groups
    self.mock_utils._GetUser.return_value = pw_entry
    self.mock_utils._AddUser.return_value = True
    self.mock_utils._UpdateUserGroups.return_value = True
    for user in valid_users:
      self.assertTrue(
          accounts_utils.AccountsUtils.UpdateUser(self.mock_utils, user, keys))
      self.mock_utils._UpdateSudoer.assert_called_once_with(user, sudoer=True)
      self.mock_utils._UpdateSudoer.reset_mock()
      self.mock_utils._UpdateAuthorizedKeys.assert_called_once_with(user, keys)
      self.mock_utils._UpdateAuthorizedKeys.reset_mock()
    self.mock_logger.warning.assert_not_called()

  def testUpdateUserInvalidUser(self):
    self.mock_utils._GetUser = mock.Mock()
    invalid_users = [
        '',
        '!#$%^',
        '-abc',
        '#abc',
        '^abc',
        'abc*xyz',
        'abc xyz',
        'xyz*',
        'xyz$',
        'areallylongusernamethatexceedsthethirtytwocharacterlimit'
    ]
    for user in invalid_users:
      self.assertFalse(
          accounts_utils.AccountsUtils.UpdateUser(self.mock_utils, user, []))
      self.mock_logger.warning.assert_called_once_with(mock.ANY, user)
      self.mock_logger.reset_mock()
    self.mock_utils._GetUser.assert_not_called()

  def testUpdateUserFailedAddUser(self):
    self.mock_utils._UpdateUserGroups = mock.Mock()
    user = 'user'
    self.mock_utils._GetUser.return_value = False
    self.mock_utils._AddUser.return_value = False

    self.assertFalse(
        accounts_utils.AccountsUtils.UpdateUser(self.mock_utils, user, []))
    self.mock_utils._GetUser.assert_called_once_with(user)
    self.mock_utils._AddUser.assert_called_once_with(user)

  def testUpdateUserFailedUpdateGroups(self):
    user = 'user'
    groups = ['a', 'b', 'c']
    self.mock_utils.groups = groups
    self.mock_utils._GetUser.return_value = False
    self.mock_utils._AddUser.return_value = True
    self.mock_utils._UpdateUserGroups.return_value = False

    self.assertFalse(
        accounts_utils.AccountsUtils.UpdateUser(self.mock_utils, user, []))
    self.mock_utils._GetUser.assert_called_once_with(user)
    self.mock_utils._AddUser.assert_called_once_with(user)
    self.mock_utils._UpdateUserGroups.assert_called_once_with(user, groups)

  def testUpdateUserNoLogin(self):
    self.mock_utils._UpdateAuthorizedKeys = mock.Mock()
    user = 'user'
    groups = ['a', 'b', 'c']
    pw_shell = '/sbin/nologin'
    pw_entry = accounts_utils.pwd.struct_passwd(
        ('', '', '', '', '', '', pw_shell))
    self.mock_utils.groups = groups
    self.mock_utils._GetUser.return_value = pw_entry
    self.mock_utils._UpdateUserGroups.return_value = True

    self.assertTrue(
        accounts_utils.AccountsUtils.UpdateUser(self.mock_utils, user, []))
    self.mock_utils._UpdateSudoer.assert_called_once_with(user, sudoer=True)
    self.mock_utils._UpdateAuthorizedKeys.assert_not_called()

  def testUpdateUserSudoersError(self):
    user = 'user'
    groups = ['a', 'b', 'c']
    keys = ['Key 1', 'Key 2']
    pw_entry = accounts_utils.pwd.struct_passwd(tuple(['']*7))
    self.mock_utils.groups = groups
    self.mock_utils._GetUser.return_value = pw_entry
    self.mock_utils._UpdateSudoer.return_value = False

    self.assertFalse(
        accounts_utils.AccountsUtils.UpdateUser(self.mock_utils, user, keys))
    self.mock_utils._GetUser.assert_called_once_with(user)
    self.mock_utils._UpdateSudoer.assert_called_once_with(user, sudoer=True)

  def testUpdateUserError(self):
    user = 'user'
    groups = ['a', 'b', 'c']
    keys = ['Key 1', 'Key 2']
    pw_entry = accounts_utils.pwd.struct_passwd(tuple(['']*7))
    self.mock_utils.groups = groups
    self.mock_utils._GetUser.return_value = pw_entry
    self.mock_utils._AddUser.return_value = True
    self.mock_utils._UpdateAuthorizedKeys.side_effect = IOError('Test Error')

    self.assertFalse(
        accounts_utils.AccountsUtils.UpdateUser(self.mock_utils, user, keys))
    self.mock_logger.warning.assert_called_once_with(mock.ANY, user, mock.ANY)

  @mock.patch('google_compute_engine.accounts.accounts_utils.subprocess.check_call')
  def testRemoveUser(self, mock_call):
    user = 'user'
    self.mock_utils.remove = False

    accounts_utils.AccountsUtils.RemoveUser(self.mock_utils, user)
    self.mock_utils._RemoveAuthorizedKeys.assert_called_once_with(user)
    self.mock_utils._UpdateSudoer.assert_called_once_with(user, sudoer=False)
    mock_call.assert_not_called()

  @mock.patch('google_compute_engine.accounts.accounts_utils.subprocess.check_call')
  def testRemoveUserForce(self, mock_call):
    user = 'user'
    command = self.userdel_cmd.format(user=user)
    self.mock_utils.remove = True

    accounts_utils.AccountsUtils.RemoveUser(self.mock_utils, user)
    mock.call.assert_called_once_with(command.split(' ')),
    expected_calls = [mock.call.info(mock.ANY, user)] * 2
    self.assertEqual(self.mock_logger.mock_calls, expected_calls)
    self.mock_utils._RemoveAuthorizedKeys.assert_called_once_with(user)
    self.mock_utils._UpdateSudoer.assert_called_once_with(user, sudoer=False)

  @mock.patch('google_compute_engine.accounts.accounts_utils.subprocess.check_call')
  def testRemoveUserError(self, mock_call):
    user = 'user'
    command = self.userdel_cmd.format(user=user)
    mock_call.side_effect = subprocess.CalledProcessError(1, 'Test')
    self.mock_utils.remove = True

    accounts_utils.AccountsUtils.RemoveUser(self.mock_utils, user)
    mock.call.assert_called_once_with(command.split(' ')),
    expected_calls = [
        mock.call.info(mock.ANY, user),
        mock.call.warning(mock.ANY, user, mock.ANY),
    ]
    self.assertEqual(self.mock_logger.mock_calls, expected_calls)
    self.mock_utils._RemoveAuthorizedKeys.assert_called_once_with(user)
    self.mock_utils._UpdateSudoer.assert_called_once_with(user, sudoer=False)


if __name__ == '__main__':
  unittest.main()
