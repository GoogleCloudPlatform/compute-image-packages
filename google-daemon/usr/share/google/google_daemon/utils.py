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

"""Library functions and interfaces for manipulating accounts."""

import errno
import fcntl
import logging
import logging.handlers
import os
import shutil
import subprocess
import sys
import tempfile

class RunCommandException(Exception):
  """Could not run a command."""
  pass


class System(object):
  """Interface for interacting with the system."""

  def __init__(self, subprocess_module=subprocess, os_module=os):
    self.subprocess = subprocess_module
    self.os = os_module

  def MakeLoggingHandler(self, prefix, facility):
    """Make a logging handler to send logs to syslog."""
    handler = logging.handlers.SysLogHandler(
        address='/dev/log', facility=facility)
    formatter = logging.Formatter(prefix + ': %(levelname)s %(message)s')
    handler.setFormatter(formatter)
    return handler

  def SetLoggingHandler(self, logger, handler):
    """Setup logging w/ a specific handler."""
    handler.setLevel(logging.INFO)
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

  def EnableDebugLogging(self, logger):
    debug_handler = logging.StreamHandler(sys.stdout)
    debug_handler.setLevel(logging.DEBUG)
    logger.addHandler(debug_handler)
    logger.setLevel(logging.DEBUG)

  def OpenFile(self, *args, **kwargs):
    return open(*args, **kwargs)

  def MoveFile(self, src, dst):
    return shutil.move(src, dst)

  def CreateTempFile(self, delete=True):
    return tempfile.NamedTemporaryFile(delete=delete)

  def DeleteFile(self, name):
    return os.remove(name)

  def UserAdd(self, user, groups):
    logging.info('Creating account %s', user)

    # We must set the crypto passwd via useradd to '*' to make ssh work
    # on Linux systems without PAM.
    #
    # Unfortunately, there is no spec that I can find that defines how
    # this stuff is used and from the manpage of shadow it says that "!"
    # or "*" or any other invalid crypt can be used.
    #
    # ssh just takes it upon itself to use "!" as its locked account token:
    # https://github.com/openssh/openssh-portable/blob/master/configure.ac#L705
    #
    # If '!' token is used then it simply denies logins:
    # https://github.com/openssh/openssh-portable/blob/master/auth.c#L151
    #
    # To solve the issue make the passwd '*' which is also recognized as
    # locked but doesn't prevent ssh logins.
    result = self.RunCommand([
        '/usr/sbin/useradd', user, '-m', '-s', '/bin/bash', '-p', '*', '-G',
        ','.join(groups)])
    if self.RunCommandFailed(result, 'Could not create user %s', user):
      return False
    return True

  def IsValidSudoersFile(self, filename):
    result = self.RunCommand(['/usr/sbin/visudo', '-c', '-f', filename])
    if result[0] != 0:
      with self.system.OpenFile(filename, 'r') as f:
        contents = f.read()
      self.RunCommandFailed(
          result, 'Could not produce valid sudoers file\n%s' % contents)
      return False
    return True

  def IsExecutable(self, path):
    """Return whether path exists and is an executable binary."""
    return self.os.path.isfile(path) and self.os.access(path, os.X_OK)

  def RunCommand(self, args):
    """Run a command, return a retcode, stdout, stderr tuple."""
    try:
      p = self.subprocess.Popen(
          args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
      (stdout, stderr) = p.communicate()
      return (p.returncode, stdout, stderr)
    except OSError, e:
      raise RunCommandException('Could not run %s due to %s' % (args, e))

  def RunCommandFailed(self, result, *msg_args):
    retcode, stdout, stderr = result
    if retcode != 0:
      logging.warning('%s\nSTDOUT:\n%s\nSTDERR:\n%s\n',
                      msg_args[0] % msg_args[1:], stdout, stderr)
      return True
    return False


class CouldNotLockException(Exception):
  """Someone else seems to be holding the lock."""
  pass


class UnexpectedLockException(Exception):
  """We genuinely failed to lock the file."""
  pass


class CouldNotUnlockException(Exception):
  """Someone else seems to be holding the lock."""
  pass


class UnexpectedUnlockException(Exception):
  """We genuinely failed to unlock the file."""
  pass


class LockFile(object):
  """Lock a file to prevent multiple concurrent executions."""

  def __init__(self, fcntl_module=fcntl):
    self.fcntl_module = fcntl_module

  def RunExclusively(self, lock_fname, method):
    try:
      self.Lock(lock_fname)
      method()
      self.Unlock()
    except CouldNotLockException:
      logging.warning(
          'Could not lock %s.  Is it locked by another program?',
          lock_fname)
    except UnexpectedLockException as e:
      logging.warning(
          'Could not lock %s due to %s', lock_fname, e)
    except CouldNotUnlockException:
      logging.warning(
          'Could not unlock %s. Is it locked by another program?',
          lock_fname)
    except UnexpectedUnlockException as e:
      logging.warning(
          'Could not unlock %s due to %s', lock_fname, e)

  def Lock(self, lock_fname):
    """Lock the lock file."""
    try:
      self.fh = open(lock_fname, 'w+b')
      self.fcntl_module.flock(self.fh.fileno(), fcntl.LOCK_EX|fcntl.LOCK_NB)
    except IOError as e:
      if e.errno == errno.EWOULDBLOCK:
        raise CouldNotLockException()
      raise UnexpectedLockException('Failed to lock: %s' % e)

  def Unlock(self):
    """Unlock the lock file."""
    try:
      self.fcntl_module.flock(self.fh.fileno(), fcntl.LOCK_UN|fcntl.LOCK_NB)
    except IOError as e:
      if e.errno == errno.EWOULDBLOCK:
        raise CouldNotUnlockException()
      raise UnexpectedUnlockException('Failed to unlock: %s' % e)
