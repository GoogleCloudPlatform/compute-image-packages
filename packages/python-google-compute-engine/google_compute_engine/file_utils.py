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

"""A library providing file utilities for setting permissions and locking."""

import contextlib
import errno
import fcntl
import os
import subprocess


def _SetSELinuxContext(path):
  """Set the appropriate SELinux context, if SELinux tools are installed.

  Calls /sbin/restorecon on the provided path to set the SELinux context as
  specified by policy. This call does not operate recursively.

  Only some OS configurations use SELinux. It is therefore acceptable for
  restorecon to be missing, in which case we do nothing.

  Args:
    path: string, the path on which to fix the SELinux context.
  """
  restorecon = '/sbin/restorecon'
  if os.path.isfile(restorecon) and os.access(restorecon, os.X_OK):
    subprocess.call([restorecon, path])


def SetPermissions(path, mode=None, uid=None, gid=None, mkdir=False):
  """Set the permissions and ownership of a path.

  Args:
    path: string, the path for which owner ID and group ID needs to be setup.
    mode: octal string, the permissions to set on the path.
    uid: int, the owner ID to be set for the path.
    gid: int, the group ID to be set for the path.
    mkdir: bool, True if the directory needs to be created.
  """
  if mkdir and not os.path.exists(path):
    os.mkdir(path, mode or 0o777)
  elif mode:
    os.chmod(path, mode)
  if uid and gid:
    os.chown(path, uid, gid)
  _SetSELinuxContext(path)


def Lock(fd, path, blocking):
  """Lock the provided file descriptor.

  Args:
    fd: int, the file descriptor of the file to lock.
    path: string, the name of the file to lock.
    blocking: bool, whether the function should return immediately.

  Raises:
    IOError, raised from flock while attempting to lock a file.
  """
  operation = fcntl.LOCK_EX if blocking else fcntl.LOCK_EX | fcntl.LOCK_NB
  try:
    fcntl.flock(fd, operation)
  except IOError as e:
    if e.errno == errno.EWOULDBLOCK:
      raise IOError('Exception locking %s. File already locked.' % path)
    else:
      raise IOError('Exception locking %s. %s.' % (path, str(e)))


def Unlock(fd, path):
  """Release the lock on the file.

  Args:
    fd: int, the file descriptor of the file to unlock.
    path: string, the name of the file to lock.

  Raises:
    IOError, raised from flock while attempting to release a file lock.
  """
  try:
    fcntl.flock(fd, fcntl.LOCK_UN | fcntl.LOCK_NB)
  except IOError as e:
    if e.errno == errno.EWOULDBLOCK:
      raise IOError('Exception unlocking %s. Locked by another process.' % path)
    else:
      raise IOError('Exception unlocking %s. %s.' % (path, str(e)))


@contextlib.contextmanager
def LockFile(path, blocking=False):
  """Interface to flock-based file locking to prevent concurrent executions.

  Args:
    path: string, the name of the file to lock.
    blocking: bool, whether the function should return immediately.

  Yields:
    None, yields when a lock on the file is obtained.

  Raises:
    IOError, raised from flock locking operations on a file.
    OSError, raised from file operations.
  """
  fd = os.open(path, os.O_CREAT)
  try:
    Lock(fd, path, blocking)
    yield
  finally:
    try:
      Unlock(fd, path)
    finally:
      os.close(fd)
