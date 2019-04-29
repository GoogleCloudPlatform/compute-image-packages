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

"""Utilities for provisioning or deprovisioning a Linux user account."""

import grp
import os
import pwd
import re
import shutil
import subprocess
import tempfile

from google_compute_engine import constants
from google_compute_engine import file_utils

USER_REGEX = re.compile(r'\A[A-Za-z0-9._][A-Za-z0-9._-]{0,31}\Z')
DEFAULT_GPASSWD_ADD_CMD = 'gpasswd -a {user} {group}'
DEFAULT_GPASSWD_REMOVE_CMD = 'gpasswd -d {user} {group}'
DEFAULT_GROUPADD_CMD = 'groupadd {group}'
DEFAULT_USERADD_CMD = 'useradd -m -s /bin/bash -p * {user}'
DEFAULT_USERDEL_CMD = 'userdel -r {user}'
DEFAULT_USERMOD_CMD = 'usermod -G {groups} {user}'


class AccountsUtils(object):
  """System user account configuration utilities."""

  google_comment = '# Added by Google'

  def __init__(
      self, logger, groups=None, remove=False, gpasswd_add_cmd=None,
      gpasswd_remove_cmd=None, groupadd_cmd=None, useradd_cmd=None,
      userdel_cmd=None, usermod_cmd=None):
    """Constructor.

    Args:
      logger: logger object, used to write to SysLog and serial port.
      groups: string, a comma separated list of groups.
      remove: bool, True if deprovisioning a user should be destructive.
      gpasswd_add_cmd: string, command to add an user to a group.
      gpasswd_remove_cmd: string, command to remove an user from a group.
      groupadd_cmd: string, command to add a new group.
      useradd_cmd: string, command to create a new user.
      userdel_cmd: string, command to delete a user.
      usermod_cmd: string, command to modify user's groups.
    """
    self.gpasswd_add_cmd = gpasswd_add_cmd or DEFAULT_GPASSWD_ADD_CMD
    self.gpasswd_remove_cmd = gpasswd_remove_cmd or DEFAULT_GPASSWD_REMOVE_CMD
    self.groupadd_cmd = groupadd_cmd or DEFAULT_GROUPADD_CMD
    self.useradd_cmd = useradd_cmd or DEFAULT_USERADD_CMD
    self.userdel_cmd = userdel_cmd or DEFAULT_USERDEL_CMD
    self.usermod_cmd = usermod_cmd or DEFAULT_USERMOD_CMD
    self.logger = logger
    self.google_sudoers_group = 'google-sudoers'
    self.google_sudoers_file = (
        constants.LOCALBASE + '/etc/sudoers.d/google_sudoers')
    self.google_users_dir = constants.LOCALBASE + '/var/lib/google'
    self.google_users_file = os.path.join(self.google_users_dir, 'google_users')

    self._CreateSudoersGroup()
    self.groups = groups.split(',') if groups else []
    self.groups = list(filter(self._GetGroup, self.groups))
    self.remove = remove

  def _GetGroup(self, group):
    """Retrieve a Linux group.

    Args:
      group: string, the name of the Linux group to retrieve.

    Returns:
      grp.struct_group, the Linux group or None if it does not exist.
    """
    try:
      return grp.getgrnam(group)
    except KeyError:
      return None

  def _CreateSudoersGroup(self):
    """Create a Linux group for Google added sudo user accounts."""
    if not self._GetGroup(self.google_sudoers_group):
      try:
        command = self.groupadd_cmd.format(group=self.google_sudoers_group)
        subprocess.check_call(command.split(' '))
      except subprocess.CalledProcessError as e:
        self.logger.warning('Could not create the sudoers group. %s.', str(e))

    if not os.path.exists(self.google_sudoers_file) or os.path.getsize(self.google_sudoers_file) == 0:
      try:
        with open(self.google_sudoers_file, 'w') as group:
          message = '%{0} ALL=(ALL:ALL) NOPASSWD:ALL'.format(
              self.google_sudoers_group)
          group.write(message)
      except IOError as e:
        self.logger.error(
            'Could not write sudoers file. %s. %s',
            self.google_sudoers_file, str(e))
        return

    file_utils.SetPermissions(
        self.google_sudoers_file, mode=0o440, uid=0, gid=0)

  def _GetUser(self, user):
    """Retrieve a Linux user account.

    Args:
      user: string, the name of the Linux user account to retrieve.

    Returns:
      pwd.struct_passwd, the Linux user or None if it does not exist.
    """
    try:
      return pwd.getpwnam(user)
    except KeyError:
      return None

  def _AddUser(self, user):
    """Configure a Linux user account.

    Args:
      user: string, the name of the Linux user account to create.

    Returns:
      bool, True if user creation succeeded.
    """
    self.logger.info('Creating a new user account for %s.', user)

    command = self.useradd_cmd.format(user=user)
    try:
      subprocess.check_call(command.split(' '))
    except subprocess.CalledProcessError as e:
      self.logger.warning('Could not create user %s. %s.', user, str(e))
      return False
    else:
      self.logger.info('Created user account %s.', user)
      return True

  def _UpdateUserGroups(self, user, groups):
    """Update group membership for a Linux user.

    Args:
      user: string, the name of the Linux user account.
      groups: list, the group names to add the user as a member.

    Returns:
      bool, True if user update succeeded.
    """
    groups = ','.join(groups)
    self.logger.debug('Updating user %s with groups %s.', user, groups)
    command = self.usermod_cmd.format(user=user, groups=groups)
    try:
      subprocess.check_call(command.split(' '))
    except subprocess.CalledProcessError as e:
      self.logger.warning('Could not update user %s. %s.', user, str(e))
      return False
    else:
      self.logger.debug('Updated user account %s.', user)
      return True

  def _UpdateAuthorizedKeys(self, user, ssh_keys):
    """Update the authorized keys file for a Linux user with a list of SSH keys.

    Args:
      user: string, the name of the Linux user account.
      ssh_keys: list, the SSH key strings associated with the user.

    Raises:
      IOError, raised when there is an exception updating a file.
      OSError, raised when setting permissions or writing to a read-only
          file system.
    """
    pw_entry = self._GetUser(user)
    if not pw_entry:
      return

    uid = pw_entry.pw_uid
    gid = pw_entry.pw_gid
    home_dir = pw_entry.pw_dir
    ssh_dir = os.path.join(home_dir, '.ssh')

    # Not all sshd's support multiple authorized_keys files so we have to
    # share one with the user. We add each of our entries as follows:
    #  # Added by Google
    #  authorized_key_entry
    authorized_keys_file = os.path.join(ssh_dir, 'authorized_keys')

    # Do not write to the authorized keys file if it is a symlink.
    if os.path.islink(ssh_dir) or os.path.islink(authorized_keys_file):
      self.logger.warning(
          'Not updating authorized keys for user %s. File is a symlink.', user)
      return

    # Create home directory if it does not exist. This can happen if _GetUser
    # (getpwnam) returns non-local user info (e.g., from LDAP).
    if not os.path.exists(home_dir):
        file_utils.SetPermissions(home_dir, mode=0o755, uid=uid, gid=gid,
            mkdir=True)

    # Create ssh directory if it does not exist.
    file_utils.SetPermissions(ssh_dir, mode=0o700, uid=uid, gid=gid, mkdir=True)

    # Create entry in the authorized keys file.
    prefix = self.logger.name + '-'
    with tempfile.NamedTemporaryFile(
        mode='w', prefix=prefix, delete=True) as updated_keys:
      updated_keys_file = updated_keys.name
      if os.path.exists(authorized_keys_file):
        lines = open(authorized_keys_file).readlines()
      else:
        lines = []

      google_lines = set()
      for i, line in enumerate(lines):
        if line.startswith(self.google_comment):
          google_lines.update([i, i+1])

      # Write user's authorized key entries.
      for i, line in enumerate(lines):
        if i not in google_lines and line:
          line += '\n' if not line.endswith('\n') else ''
          updated_keys.write(line)

      # Write the Google authorized key entries at the end of the file.
      # Each entry is preceded by '# Added by Google'.
      for ssh_key in ssh_keys:
        ssh_key += '\n' if not ssh_key.endswith('\n') else ''
        updated_keys.write('%s\n' % self.google_comment)
        updated_keys.write(ssh_key)

      # Write buffered data to the updated keys file without closing it and
      # update the Linux user's authorized keys file.
      updated_keys.flush()
      shutil.copy(updated_keys_file, authorized_keys_file)

    file_utils.SetPermissions(
        authorized_keys_file, mode=0o600, uid=uid, gid=gid)

  def _UpdateSudoer(self, user, sudoer=False):
    """Update sudoer group membership for a Linux user account.

    Args:
      user: string, the name of the Linux user account.
      sudoer: bool, True if the user should be a sudoer.

    Returns:
      bool, True if user update succeeded.
    """
    if sudoer:
      self.logger.info('Adding user %s to the Google sudoers group.', user)
      command = self.gpasswd_add_cmd.format(
          user=user, group=self.google_sudoers_group)
    else:
      self.logger.info('Removing user %s from the Google sudoers group.', user)
      command = self.gpasswd_remove_cmd.format(
          user=user, group=self.google_sudoers_group)

    try:
      subprocess.check_call(command.split(' '))
    except subprocess.CalledProcessError as e:
      self.logger.warning('Could not update user %s. %s.', user, str(e))
      return False
    else:
      self.logger.debug('Removed user %s from the Google sudoers group.', user)
      return True

  def _RemoveAuthorizedKeys(self, user):
    """Remove a Linux user account's authorized keys file to prevent login.

    Args:
      user: string, the Linux user account to remove access.
    """
    pw_entry = self._GetUser(user)
    if not pw_entry:
      return

    home_dir = pw_entry.pw_dir
    authorized_keys_file = os.path.join(home_dir, '.ssh', 'authorized_keys')
    if os.path.exists(authorized_keys_file):
      try:
        os.remove(authorized_keys_file)
      except OSError as e:
        message = 'Could not remove authorized keys for user %s. %s.'
        self.logger.warning(message, user, str(e))

  def GetConfiguredUsers(self):
    """Retrieve the list of configured Google user accounts.

    Returns:
      list, the username strings of users congfigured by Google.
    """
    if os.path.exists(self.google_users_file):
      users = open(self.google_users_file).readlines()
    else:
      users = []
    return [user.strip() for user in users]

  def SetConfiguredUsers(self, users):
    """Set the list of configured Google user accounts.

    Args:
      users: list, the username strings of the Linux accounts.
    """
    prefix = self.logger.name + '-'
    with tempfile.NamedTemporaryFile(
        mode='w', prefix=prefix, delete=True) as updated_users:
      updated_users_file = updated_users.name
      for user in users:
        updated_users.write(user + '\n')
      updated_users.flush()
      if not os.path.exists(self.google_users_dir):
        os.makedirs(self.google_users_dir)
      shutil.copy(updated_users_file, self.google_users_file)

    file_utils.SetPermissions(self.google_users_file, mode=0o600, uid=0, gid=0)

  def UpdateUser(self, user, ssh_keys):
    """Update a Linux user with authorized SSH keys.

    Args:
      user: string, the name of the Linux user account.
      ssh_keys: list, the SSH key strings associated with the user.

    Returns:
      bool, True if the user account updated successfully.
    """
    if not bool(USER_REGEX.match(user)):
      self.logger.warning('Invalid user account name %s.', user)
      return False
    if not self._GetUser(user):
      # User does not exist. Attempt to create the user and add them to the
      # appropriate user groups.
      if not (self._AddUser(user)
              and self._UpdateUserGroups(user, self.groups)):
        return False
    # Add the user to the google sudoers group.
    if not self._UpdateSudoer(user, sudoer=True):
      return False

    # Don't try to manage account SSH keys with a shell set to disable
    # logins. This helps avoid problems caused by operator and root sharing
    # a home directory in CentOS and RHEL.
    pw_entry = self._GetUser(user)
    if pw_entry and os.path.basename(pw_entry.pw_shell) == 'nologin':
      message = 'Not updating user %s. User set `nologin` as login shell.'
      self.logger.debug(message, user)
      return True

    try:
      self._UpdateAuthorizedKeys(user, ssh_keys)
    except (IOError, OSError) as e:
      message = 'Could not update the authorized keys file for user %s. %s.'
      self.logger.warning(message, user, str(e))
      return False
    else:
      return True

  def RemoveUser(self, user):
    """Remove a Linux user account.

    Args:
      user: string, the Linux user account to remove.
    """
    self.logger.info('Removing user %s.', user)
    if self.remove:
      command = self.userdel_cmd.format(user=user)
      try:
        subprocess.check_call(command.split(' '))
      except subprocess.CalledProcessError as e:
        self.logger.warning('Could not remove user %s. %s.', user, str(e))
      else:
        self.logger.info('Removed user account %s.', user)
    self._RemoveAuthorizedKeys(user)
    self._UpdateSudoer(user, sudoer=False)
