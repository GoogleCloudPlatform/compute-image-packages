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

"""Tool for running account manager as a daemon."""

import fcntl
import logging
import os
import signal

PIDFILE = '/var/run/manage_accounts.pid'


class AccountsManagerDaemon(object):
  """Creates a daemon process to run the accounts manager in."""

  def __init__(self, pidfile, accounts_manager, fcntl_module=fcntl):
    logging.debug('Initializing Daemon Module')
    if not pidfile:
      pidfile = PIDFILE

    self.pidfile = pidfile
    self.accounts_manager = accounts_manager
    self.fcntl_module = fcntl_module

  def StartDaemon(self):
    """Spins off a process that runs as a daemon."""
    # To spin off the process, use what seems to be the "standard" way to spin
    # off daemons: fork a child process, make it the session and process group
    # leader, then fork it again so that the actual daemon process is no longer
    # a session leader.
    #
    # This is a very simplified (with significantly reduced features) version of
    # the python-daemon library at https://pypi.python.org/pypi/python-daemon/.
    pid = os.fork()
    logging.debug('Forked new process, pid= {0}'.format(pid))
    if pid == 0:
      os.setsid()
      pid = os.fork()
      if pid == 0:
        os.chdir('/')
        os.umask(0)
      else:
        # The use of os._exit here is recommended for parents of a daemon
        # process to avoid issues with running the cleanup tasks that
        # sys.exit() runs by preventing issues from the cleanup being run
        # more than once when the two parents exit and later when the daemon
        # exits.
        os._exit(0)
    else:
      os._exit(0)

    # Set up pidfile and signal handlers.
    pidf = open(self.pidfile, 'w')
    pidf.write(str(os.getpid()))
    pidf.close()

    logging.debug('Sending signal SIGTERM to shutdown daemon')
    signal.signal(signal.SIGTERM, self.ShutdownDaemon)

    self.accounts_manager.Main()

  def ShutdownDaemon(self, signal_number, unused_stack_frame):
    # Grab the lock on the lock file, ensuring that the accounts manager is not
    # in the middle of something. Using a different file reference guarantees
    # that the lock can only be grabbed once the accounts manager is done with
    # it and holding it guarantees that the accounts manager won't start up
    # again while shutting down.
    logging.debug('Acquiring Daemon lock.')
    lockfile = open(self.accounts_manager.lock_fname, 'r')
    self.fcntl_module.flock(lockfile.fileno(), fcntl.LOCK_EX)

    logging.debug('Shutting down Daemon module.')
    # Clean up pidfile and terminate. Lock will be released with termination.
    os.remove(self.pidfile)
    exception = SystemExit('Terminating on signal number %d' % signal_number)
    raise exception
