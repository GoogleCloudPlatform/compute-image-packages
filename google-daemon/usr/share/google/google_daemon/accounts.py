#!/usr/bin/python
# Copyright 2013 Google Inc. All Rights Reserved.
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

"""Update accounts needed on this GCE instance.

Update accounts based on the contents of ACCOUNTS_URL, which should contain a
newline-delimited file of accounts and SSH public keys. Each line represents a
SSH public key which should be allowed to log in to that account.

If the account does not already exist on the system, it is created and added
to /etc/sudoers to allow that account to administer the machine without needing
a password.
"""

import errno
import grp
import logging
import os
import pwd
import re
import stat
import tempfile
import time


def EnsureTrailingNewline(line):
  if line.endswith('\n'):
    return line
  return line + '\n'


def IsUserSudoerInLines(user, sudoer_lines):
  """Return whether the user has an entry in the sudoer lines."""

  def IsUserSudoerEntry(line):
    return re.match(r'^%s\s+' % user, line)

  return filter(IsUserSudoerEntry, sudoer_lines)


class Accounts(object):
  """Manage accounts on a machine."""

  # Comes from IEEE Std 1003.1-2001.  Characters from the portable
  # filename character set.  The hyphen should not be the first char
  # of a portable user name.
  VALID_USERNAME_CHARS = set(
      map(chr, range(ord('A'), ord('Z') + 1)) +
      map(chr, range(ord('a'), ord('z') + 1)) +
      map(chr, range(ord('0'), ord('9') + 1)) +
      ['_', '-', '.'])

  def __init__(self, grp_module=grp, os_module=os,
               pwd_module=pwd, system_module=None,
               urllib2_module=None, time_module=time):
    """Construct an Accounts given the module injections."""
    self.system_module = system_module

    self.grp = grp_module
    self.os = os_module
    self.pwd = pwd_module
    self.system = system_module
    self.time_module = time_module
    self.urllib2 = urllib2_module

    self.default_user_groups = self.GroupsThatExist(
        ['adm', 'video', 'dip', 'plugdev', 'sudo'])

  def UpdateUser(self, username, ssh_keys):
    """Create username on the system, with authorized ssh_keys."""

    if not self.IsValidUsername(username):
      logging.warning(
          'Not creating account for user %s.  Usernames must comprise'
          ' characters [A-Za-z0-9._-] and not start with \'-\'.', username)
      return

    if not self.UserExists(username):
      self.system.UserAdd(username, self.default_user_groups)

    if self.UserExists(username):
      # Don't try to manage the sshkeys of an account with a shell set to
      # disable logins.  Helps avoid problems caused by operator and root
      # sharing a home directory in CentOS and RHEL
      if self.UserNoLogin(username):
        logging.debug(
            'Not processing account for user %s.  User has /sbin/nologin'
            ' set as login shell', username)
        return

      # If we're just removing keys from a user who may have been in the
      # metadata server but isn't currently, we should never increase their
      # privileges. Therefore, only grant sudo access if we have ssh keys.
      if ssh_keys:
        self.MakeUserSudoer(username)
      self.AuthorizeSshKeys(username, ssh_keys)

  def IsValidUsername(self, username):
    """Return whether username looks like a valid user name."""

    def InvalidCharacterFilter(c):
      return c not in Accounts.VALID_USERNAME_CHARS

    if filter(InvalidCharacterFilter, username):
      # There's an invalid character in it.
      return False

    if username.startswith('-'):
      return False

    return True

  def GroupsThatExist(self, groups_list):
    """Return all the groups in groups_list that exist on the machine."""

    def GroupExists(group):
      try:
        self.grp.getgrnam(group)
        return True
      except KeyError:
        return False

    return filter(GroupExists, groups_list)

  def GetUserInfo(self, user):
    """Return a tuple of the user's (home_dir, pid, gid)."""
    pwent = self.pwd.getpwnam(user)
    return (pwent.pw_dir, pwent.pw_uid, pwent.pw_gid)

  def UserExists(self, user):
    """Test whether a given user exists or not."""
    try:
      self.pwd.getpwnam(user)
      return True
    except KeyError:
      return False

  def UserNoLogin(self, user):
    """Test whether a user's shell is /sbin/nologin."""
    pwent = self.pwd.getpwnam(user)
    return pwent.pw_shell == '/sbin/nologin'

  def LockSudoers(self):
    """Create an advisory lock on /etc/sudoers.tmp.

    Returns:
      True if successful, False if not.
    """
    try:
      f = self.os.open('/etc/sudoers.tmp', os.O_EXCL|os.O_CREAT)
      self.os.close(f)
      return True
    except OSError as e:
      if e.errno == errno.EEXIST:
        logging.warning('/etc/sudoers.tmp lock file already exists')
      else:
        logging.warning('Could not create /etc/sudoers.tmp lock file: %s', e)
    return False

  def UnlockSudoers(self):
    """Remove the advisory lock on /etc/sudoers.tmp."""
    try:
      self.os.unlink('/etc/sudoers.tmp')
      return True
    except OSError as e:
      if e.errno == errno.ENOENT:
        return True
      logging.warning('Could not remove /etc/sudoers.tmp: %s', e)
      return False

  def MakeUserSudoer(self, user):
    """Add user to the sudoers file."""
    # If the user has no sudoers file, don't add an entry.
    if not self.os.path.isfile('/etc/sudoers'):
      logging.info('Did not grant admin access to %s. /etc/sudoers not found.',
                   user)
      return

    with self.system.OpenFile('/etc/sudoers', 'r') as sudoer_f:
      sudoer_lines = sudoer_f.readlines()

    if IsUserSudoerInLines(user, sudoer_lines):
      # User is already sudoer.  Done.  We don't have to check for a lock
      # file.
      return

    # Lock sudoers.
    if not self.LockSudoers():
      logging.warning('Did not grant admin access to %s. /etc/sudoers locked.',
                      user)
      return

    try:
      # First read in the sudoers file (this time under the lock).
      with self.system.OpenFile('/etc/sudoers', 'r') as sudoer_f:
        sudoer_lines = sudoer_f.readlines()

      if IsUserSudoerInLines(user, sudoer_lines):
        # User is already sudoer.  Done.
        return

      # Create a temporary sudoers file with the contents we want.
      sudoer_lines.append('%s ALL=NOPASSWD: ALL' % user)
      sudoer_lines = [EnsureTrailingNewline(line) for line in sudoer_lines]
      (tmp_sudoers_fd, tmp_sudoers_fname) = tempfile.mkstemp()
      with self.os.fdopen(tmp_sudoers_fd, 'w+') as tmp_sudoer_f:
        # Put the old lines.
        tmp_sudoer_f.writelines(sudoer_lines)
        tmp_sudoer_f.seek(0)

      try:
        # Validate our result.
        if not self.system.IsValidSudoersFile(tmp_sudoers_fname):
          logging.warning(
              'Did not grant admin access to %s. Sudoers was invalid.', user)
          return

        self.os.chmod('/etc/sudoers', 0640)
        with self.system.OpenFile('/etc/sudoers', 'w') as sudoer_f:
          sudoer_f.writelines(sudoer_lines)
          # Make sure we're still 0640.
          self.os.fchmod(sudoer_f.fileno(), stat.S_IWUSR | 0640)
          try:
            self.os.fchmod(sudoer_f.fileno(), 0440)
          except (IOError, OSError) as e:
            logging.warning('Could not restore perms to /etc/sudoers: %s', e)
      finally:
        # Clean up the temp file.
        try:
          self.os.unlink(tmp_sudoers_fname)
        except (IOError, OSError) as e:
          pass
    except (IOError, OSError) as e:
      logging.warning('Could not grant %s admin access: %s', user, e)
    finally:
      self.UnlockSudoers()

  def AuthorizeSshKeys(self, user, ssh_keys):
    """Add ssh_keys to the user's ssh authorized_keys.gce file."""
    (home_dir, uid, gid) = self.GetUserInfo(user)

    ssh_dir = os.path.join(home_dir, '.ssh')

    if not self.os.path.isdir(ssh_dir):
      # Create a user's ssh directory, with u+rwx as the only permissions.
      # There's proper handling and logging of OSError within EnsureDir(),
      # so neither of these calls needs th handle that.
      if not self.EnsureHomeDir(home_dir, uid, gid):
        return False

      if not self.EnsureDir(ssh_dir, uid, gid, 0700):
        return False

    # Not all sshd's support mulitple authorized_keys files.  We have to
    # share one with the user.  We add our entries as follows:
    #  # Added by Google
    #  authorized_key_entry
    authorized_keys_file = os.path.join(ssh_dir, 'authorized_keys')
    try:
      self.WriteAuthorizedSshKeysFile(authorized_keys_file, ssh_keys, uid, gid)
    except IOError as e:
      logging.warning('Could not update %s due to %s', authorized_keys_file, e)

  def SetSELinuxContext(self, path):
    """Set the appropriate SELinux context, if SELinux tools are installed.

    Calls /sbin/restorecon on the provided path to set the SELinux context as
    specified by policy. This call does not operate recursively.

    Only some OS configurations use SELinux. It is therefore acceptable for
    restorecon to be missing, in which case we do nothing.

    Arguments:
      path: The path on which to fix the SELinux context.

    Returns:
      True if successful or if restorecon is missing, False in case of error.
    """

    if self.system.IsExecutable('/sbin/restorecon'):
      result = self.system.RunCommand(['/sbin/restorecon', path])
      if self.system.RunCommandFailed(result):
        logging.error('Unable to set SELinux context for %s', path)
        return False
      else:
        return True
    else:
      logging.debug('restorecon missing; not setting SELinux context for %s',
                    path)
      return True

  def EnsureHomeDir(self, home_dir, uid, gid):
    """Make sure user's home directory exists.

    Create the directory and its ancestor directories if necessary.

    No changes are made to the ownership or permissions of a directory which
    already exists.

    Arguments:
      home_dir: The path to the home directory.
      uid: user ID to own the home dir.
      gid: group ID to own the home dir.

    Returns:
      True if successful, False if not.
    """

    if self.os.path.isdir(home_dir):
      return True

    # Use root as owner when creating ancestor directories.
    if not self.EnsureDir(home_dir, 0, 0, 0755):
      return False

    self.os.chown(home_dir, uid, gid)
    return True

  def EnsureDir(self, dir_path, uid, gid, mode):
    """Make sure the specified directory exists.

    If dir doesn't exist, create it and its ancestor directories, if necessary.

    No changes are made to the ownership or permissions of a directory which
    already exists.

    Arguments:
      dir_path: The path to the dir.
      uid: user ID of the owner.
      gid: group ID of the owner.
      mode: Permissions for the dir, as an integer (e.g. 0755).

    Returns:
      True if successful, False if not.
    """

    if self.os.path.isdir(dir_path):
      return True    # We are done

    parent_dir = self.os.path.dirname(dir_path)
    if not parent_dir == dir_path:
      if not self.EnsureDir(parent_dir, uid, gid, 0755):
        return False

    try:
      self.os.mkdir(dir_path, mode)
      self.os.chown(dir_path, uid, gid)
      self.SetSELinuxContext(dir_path)
    except OSError as e:
      if self.os.path.isdir(dir_path):
        logging.warning('Could not prepare %s: %s', dir_path, e)
        return True
      logging.error('Could not create %s: %s', dir_path, e)
      return False

    return True

  def WriteAuthorizedSshKeysFile(
      self, authorized_keys_file, ssh_keys, uid, gid):
    """Update the authorized_keys_file to contain the given ssh_keys.

    Arguments:
      authorized_keys_file: The name of the authorized keys file.
      ssh_keys: The google added ssh keys for the file.
      uid: The uid for the user.
      gid: The gid for the user.
    """
    # Create a temp file to store the new keys.
    with self.system.CreateTempFile(delete=False) as keys_file:
      new_keys_path = keys_file.name
      # Read all the ssh keys in the original key file if it exists.
      if self.os.path.exists(authorized_keys_file):
        with self.system.OpenFile(authorized_keys_file, 'r') as original_keys:
          original_keys.seek(0)
          lines = original_keys.readlines()
      else:
        lines = []

      # Pull out the # Added by Google lines.
      google_added_ixs = [i for i in range(len(lines) - 1) if
                          lines[i].startswith('# Added by Google')]
      google_added_ixs += [i + 1 for i in google_added_ixs]

      user_lines = [
          lines[i] for i in range(len(lines)) if i not in google_added_ixs]

      # First write user's entries.
      for user_line in user_lines:
        keys_file.write(EnsureTrailingNewline(user_line))

      # Put google entries at the end, each preceeded by Added by Google.
      for ssh_key in ssh_keys:
        keys_file.write('# Added by Google\n')
        keys_file.write(EnsureTrailingNewline(ssh_key))

      # Check that we have enough disk space to move the file.
      stat = self.os.statvfs(self.os.path.dirname(authorized_keys_file))
      available_space = stat.f_bavail * stat.f_bsize
      required_space = self.os.path.getsize(new_keys_path) + 1024 * 1024
      logging.debug('Writing keys file: %s bytes required; %s available.',
                    required_space, available_space)
      if available_space < required_space:
        raise IOError('Disk is too full')

    try:
      # Override the old authorized keys file with the new one.
      self.system.MoveFile(new_keys_path, authorized_keys_file)
    finally:
      try:
        self.system.DeleteFile(new_keys_path)
      except:
        pass

    # Make sure the authorized_keys_file has the right perms (u+rw).
    self.os.chmod(authorized_keys_file, 0600)
    self.os.chown(authorized_keys_file, uid, gid)

    # Set SELinux context, if applicable to this system
    self.SetSELinuxContext(authorized_keys_file)
