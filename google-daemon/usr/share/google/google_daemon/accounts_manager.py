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

"""Main driver logic for managing accounts on GCE instances."""

LOCKFILE = '/var/lock/manage-accounts.lock'


class AccountsManager(object):
  """Create accounts on a machine."""

  def __init__(self, accounts_module, desired_accounts, system, lock_file,
               lock_fname):
    """Construct an AccountsFromMetadata with the given module injections."""
    if not lock_fname:
      lock_fname = LOCKFILE
    self.accounts = accounts_module
    self.desired_accounts = desired_accounts
    self.lock_file = lock_file
    self.lock_fname = lock_fname
    self.system = system

  def Main(self):
    # Make sure that keys have been regenerated and whatnot.
    if self.system.IsExecutable('/usr/share/google/first-boot'):
      self.system.RunCommand('/usr/share/google/first-boot')

    self.lock_file.RunExclusively(self.lock_fname, self.CreateAccounts)

  def CreateAccounts(self):
    """Create all accounts that should be present."""
    desired_accounts = self.desired_accounts.GetDesiredAccounts()
    if not desired_accounts:
      return

    for username, ssh_keys in desired_accounts.iteritems():
      if not username:
        continue

      self.accounts.CreateUser(username, ssh_keys)
