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

"""A library for preventing concurrent script executions using a file lock."""

import contextlib
import errno
import fcntl
import os


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
