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

"""Manage clock skew after migration on a Google Compute Engine instance."""

import logging.handlers
import optparse
import subprocess

from google_compute_engine import config_manager
from google_compute_engine import file_utils
from google_compute_engine import logger
from google_compute_engine import metadata_watcher

LOCKFILE = '/var/lock/google_clock_skew.lock'


class ClockSkewDaemon(object):
  """Responds to drift-token changes."""

  drift_token = 'instance/virtual-clock/drift-token'

  def __init__(self, debug=False):
    """Constructor.

    Args:
      debug: bool, True if debug output should write to the console.
    """
    facility = logging.handlers.SysLogHandler.LOG_DAEMON
    self.logger = logger.Logger(
        name='google-clock-skew', debug=debug, facility=facility)
    self.watcher = metadata_watcher.MetadataWatcher(logger=self.logger)
    try:
      with file_utils.LockFile(LOCKFILE):
        self.logger.info('Starting Google Clock Skew daemon.')
        self.watcher.WatchMetadata(
            self.HandleClockSync, metadata_key=self.drift_token,
            recursive=False)
    except (IOError, OSError) as e:
      self.logger.warning(str(e))

  def HandleClockSync(self, response):
    """Called when clock drift token changes.

    Args:
      response: string, the metadata response with the new drift token value.
    """
    self.logger.info('Clock drift token has changed: %s.', response)
    command = ['/sbin/hwclock', '--hctosys']
    try:
      subprocess.check_call(command)
    except subprocess.CalledProcessError:
      self.logger.warning('Failed to sync system time with hardware clock.')
    else:
      self.logger.info('Synced system time with hardware clock.')


def main():
  parser = optparse.OptionParser()
  parser.add_option(
      '-d', '--debug', action='store_true', dest='debug',
      help='print debug output to the console.')
  (options, _) = parser.parse_args()
  instance_config = config_manager.ConfigManager()
  if instance_config.GetOptionBool('Daemons', 'clock_skew_daemon'):
    ClockSkewDaemon(debug=bool(options.debug))


if __name__ == '__main__':
  main()
