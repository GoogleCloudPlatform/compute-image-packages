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

"""Main driver logic for managing public IPs on GCE instances."""

import logging
import os
import sys

def FixPath():
  parent_dir = os.path.dirname(os.path.realpath(sys.argv[0]))
  if os.path.isdir(parent_dir):
    sys.path.append(parent_dir)


FixPath()

from utils import LockFile
from utils import System
from address_manager import AddressManager


LOCKFILE = '/var/lock/google-address-manager.lock'

def Main(system=System(), logger=logging.getLogger(), log_handler=None,
         lock_file=LockFile(), lock_fname=None):
  if not log_handler:
    log_handler = system.MakeLoggingHandler(
        'google-address-manager', logging.handlers.SysLogHandler.LOG_SYSLOG)
  system.SetLoggingHandler(logger, log_handler)
  logging.info('Starting GCE address manager')

  if not lock_fname:
    lock_fname = LOCKFILE
  manager = AddressManager(system_module=system)
  lock_file.RunExclusively(lock_fname, manager.SyncAddressesForever)


if __name__ == '__main__':
  Main()
