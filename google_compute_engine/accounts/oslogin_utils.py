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

from google_compute_engine import constants


class OsLoginUtils(object):
  """Utilities for OS Login activation."""

  def __init__(self, logger):
    """Constructor.

    Args:
      logger: logger object, used to write to SysLog and serial port.
    """
    self.logger = logger
    self.oslogin_installed = True

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

    self.oslogin_installed = True
    return not retcode

  def UpdateOsLogin(self, enable):
    """Check to see if OS Login is enabled, and switch if necessary.

    Args:
      enable: bool, enable OS Login if True, disable if False.

    Returns:
      int, the return code from updating OS Login, or None if not present.
    """
    status = self._GetStatus()
    if status is None or status == enable:
      return None

    if enable:
      action = 'activate'
      self.logger.info('Activating OS Login.')
    else:
      action = 'deactivate'
      self.logger.info('Deactivating OS Login.')

    return self._RunOsLoginControl(action)
