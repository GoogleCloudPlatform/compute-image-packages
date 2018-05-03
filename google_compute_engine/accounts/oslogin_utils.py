#!/usr/bin/python
# Copyright 2017 Google Inc. All Rights Reserved.
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

"""Utilities for provisioning or deprovisioning a Linux user account."""

import os
import subprocess
import time

from google_compute_engine import constants

NSS_CACHE_DURATION_SEC = 21600  # 6 hours in seconds.


class OsLoginUtils(object):
  """Utilities for OS Login activation."""

  def __init__(self, logger):
    """Constructor.

    Args:
      logger: logger object, used to write to SysLog and serial port.
    """
    self.logger = logger
    self.oslogin_installed = True
    self.update_time = 0

  def _RunOsLoginControl(self, action):
    """Run the OS Login control script.

    Args:
      action: str, the action to pass to the script
          (activate, deactivate, or status).

    Returns:
      int, the return code from the call, or None if the script is not found.
    """
    try:
      return subprocess.call([constants.OSLOGIN_CONTROL_SCRIPT, action])
    except OSError as e:
      if e.errno == os.errno.ENOENT:
        return None
      else:
        raise

  def _GetStatus(self):
    """Check whether OS Login is installed.

    Returns:
      bool, True if OS Login is installed.
    """
    retcode = self._RunOsLoginControl('status')
    if retcode is None:
      if self.oslogin_installed:
        self.logger.warning('OS Login not installed.')
        self.oslogin_installed = False
      return None

    # Prevent log spam when OS Login is not installed.
    self.oslogin_installed = True
    if not os.path.exists(constants.OSLOGIN_NSS_CACHE):
      return False
    return not retcode

  def _RunOsLoginNssCache(self):
    """Run the OS Login NSS cache binary.

    Returns:
      int, the return code from the call, or None if the script is not found.
    """
    try:
      return subprocess.call([constants.OSLOGIN_NSS_CACHE_SCRIPT])
    except OSError as e:
      if e.errno == os.errno.ENOENT:
        return None
      else:
        raise

  def _RemoveOsLoginNssCache(self):
    """Remove the OS Login NSS cache file."""
    if os.path.exists(constants.OSLOGIN_NSS_CACHE):
      try:
        os.remove(constants.OSLOGIN_NSS_CACHE)
      except OSError as e:
        if e.errno != os.errno.ENOENT:
          raise

  def UpdateOsLogin(self, enable, duration=NSS_CACHE_DURATION_SEC):
    """Update whether OS Login is enabled and update NSS cache if necessary.

    Args:
      enable: bool, enable OS Login if True, disable if False.
      duration: int, number of seconds before updating the NSS cache.

    Returns:
      int, the return code from updating OS Login, or None if not present.
    """
    status = self._GetStatus()
    if status is None:
      return None

    current_time = time.time()
    if status == enable:
      if status and current_time - self.update_time > duration:
        self.update_time = current_time
        return self._RunOsLoginNssCache()
      else:
        return None

    self.update_time = current_time
    if enable:
      self.logger.info('Activating OS Login.')
      return self._RunOsLoginControl('activate') or self._RunOsLoginNssCache()
    else:
      self.logger.info('Deactivating OS Login.')
      return (self._RunOsLoginControl('deactivate') or
              self._RemoveOsLoginNssCache())
