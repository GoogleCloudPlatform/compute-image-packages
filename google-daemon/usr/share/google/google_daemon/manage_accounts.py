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

import logging
import optparse
import os
import sys


def FixPath():
  parent_dir = os.path.dirname(os.path.realpath(sys.argv[0]))
  if os.path.isdir(parent_dir):
    sys.path.append(parent_dir)


FixPath()


from accounts import Accounts
from accounts_manager import AccountsManager
from accounts_manager_daemon import AccountsManagerDaemon
from desired_accounts import DesiredAccounts
from utils import LockFile
from utils import System


def Main(accounts, desired_accounts, system, logger,
         log_handler, lock_file, lock_fname=None, interval=-1,
         daemon_mode=False, debug_mode=False):
  
  if not log_handler:
    log_handler = system.MakeLoggingHandler(
        'accounts-from-metadata', logging.handlers.SysLogHandler.LOG_AUTH)
  system.SetLoggingHandler(logger, log_handler)
  
  if debug_mode:
    system.EnableDebugLogging(logger)
    logging.debug('Running in Debug Mode')

  accounts_manager = AccountsManager(
      accounts, desired_accounts, system, lock_file, lock_fname, interval)
  
  if daemon_mode:
    manager_daemon = AccountsManagerDaemon(None, accounts_manager)
    manager_daemon.StartDaemon()
  else:
    accounts_manager.Main()


if __name__ == '__main__':
  parser = optparse.OptionParser()
  parser.add_option('--daemon', dest='daemon', action='store_true')
  parser.add_option('--no-daemon', dest='daemon', action='store_false')
  parser.add_option('--interval', type='int', dest='interval')
  parser.add_option('--debug', dest='debug', action='store_true')
  parser.set_defaults(interval=60)
  parser.set_defaults(daemon=False)
  parser.set_defaults(debug=False)
  (options, args) = parser.parse_args()

  Main(Accounts(system_module=System()), DesiredAccounts(),
       System(), logging.getLogger(), None, LockFile(), None, options.interval,
       options.daemon, options.debug)
