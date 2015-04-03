#!/usr/bin/python
# Copyright 2015 Google Inc. All Rights Reserved.
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

"""Manages clock syncing after migration on GCE instances."""

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
from metadata_watcher import MetadataWatcher


LOCKFILE = '/var/lock/google-clock-sync.lock'


def HandleClockDriftToken(metadata_watcher, on_change):
  """Watches for and responds to drift-token changes.

  Args:
    metadata_watcher: a MetadataWatcher object.
    on_change: a callable to call for any change.
  """
  clock_drift_token_key = 'instance/virtual-clock/drift-token'

  def Handler(event):
    on_change(event)

  metadata_watcher.WatchMetadataForever(clock_drift_token_key,
                                        Handler, initial_value='')


def OnChange(event):
  """Called when clock drift token changes.

  Args:
    event: the new value of the drift token.
  """
  system = System()
  logging.info('Clock drift token has changed: %s', event)
  logging.info('Syncing system time with hardware clock...')
  result = system.RunCommand(['/sbin/hwclock', '--hctosys'])
  if system.RunCommandFailed(result):
    logging.error('Syncing system time failed.')
  else:
    logging.info('Synced system time with hardware clock.')


def Main(system=System(), logger=logging.getLogger(), log_handler=None,
         lock_file=LockFile(), lock_fname=None):
  if not log_handler:
    log_handler = system.MakeLoggingHandler(
        'google-clock-sync', logging.handlers.SysLogHandler.LOG_SYSLOG)
    system.SetLoggingHandler(logger, log_handler)
    logging.info('Starting GCE clock sync')

  if not lock_fname:
    lock_fname = LOCKFILE
  watcher = MetadataWatcher()
  lock_file.RunExclusively(lock_fname, HandleClockDriftToken(watcher, OnChange))


if __name__ == '__main__':
  Main()
