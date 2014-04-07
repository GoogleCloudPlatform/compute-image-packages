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

import json
import logging
import os
import time

LOCKFILE = '/var/lock/manage-accounts.lock'


class AccountsManager(object):
  """Create accounts on a machine."""

  def __init__(self, accounts_module, desired_accounts, system, lock_file,
               lock_fname, single_pass=True):
    """Construct an AccountsFromMetadata with the given module injections."""
    if not lock_fname:
      lock_fname = LOCKFILE
    self.accounts = accounts_module
    self.desired_accounts = desired_accounts
    self.lock_file = lock_file
    self.lock_fname = lock_fname
    self.system = system
    self.single_pass = single_pass

  def Main(self):
    logging.debug('AccountsManager main loop')
    # If this is a one-shot execution, then this can be run normally.
    # Otherwise, run the actual operations in a subprocess so that any
    # errors don't kill the long-lived process.
    if self.single_pass:
      self.RegenerateKeysAndCreateAccounts()
      return
    # Run this forever in a loop.
    while True:
      # Fork and run the key regeneration and account creation while the
      # parent waits for the subprocess to finish before continuing.
      
      # Create a pipe used to get the new etag value from child
      reader, writer = os.pipe() # these are file descriptors, not file objects        
      pid = os.fork()
      if pid:
        # we are the parent
        os.close(writer)
        reader = os.fdopen(reader) # turn r into a file object
        json_tags = reader.read()
        if json_tags:
          etags = json.loads(json_tags)
          if etags:
            self.desired_accounts.attributes_etag = etags[0]
            self.desired_accounts.instance_sshkeys_etag = etags[1]
        reader.close()
        logging.debug('New etag: %s', self.desired_accounts.attributes_etag)
        os.waitpid(pid, 0)
      else:
        # we are the child
        os.close(reader)
        writer = os.fdopen(writer, 'w')
        try:
          self.RegenerateKeysAndCreateAccounts()
        except Exception as e:
          logging.warning('error while trying to create accounts: %s', e)
          # An error happened while trying to create the accounts. Lets sleep a
          # bit to avoid getting stuck in a loop for intermittent errors.
          time.sleep(5)

        # Write the etag to pass to parent
        json_tags = json.dumps(
            [self.desired_accounts.attributes_etag,
             self.desired_accounts.instance_sshkeys_etag])
        writer.write(json_tags)
        writer.close()

        # The use of os._exit here is recommended for subprocesses spawned
        # by forking to avoid issues with running the cleanup tasks that
        # sys.exit() runs by preventing issues from the cleanup being run
        # once by the subprocess and once by the parent process.
        os._exit(0)

  def RegenerateKeysAndCreateAccounts(self):
    """Regenerate the keys and create accounts as needed."""
    logging.debug('RegenerateKeysAndCreateAccounts')
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
