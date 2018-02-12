#!/usr/bin/python
# Copyright 2018 Google Inc. All Rights Reserved.
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

"""Utilities that are distro specific for use on SUSE 11."""

import os
import subprocess

from google_compute_engine import constants
from google_compute_engine.distro import utils


class Utils(utils.Utils):
  """Utilities used by Linux guest services on SUSE 11."""

  def EnableNetworkInterfaces(
      self, interfaces, logger, dhclient_script=None):
    """Enable the list of network interfaces.

    Args:
      interfaces: list of string, the output device names to enable.
      logger: logger object, used to write to SysLog and serial port.
      dhclient_script: string, the path to a dhclient script used by dhclient.
    """
    interfaces_to_up = [i for i in interfaces if i != 'eth0']
    if interfaces_to_up:
      logger.info('Enabling the Ethernet interfaces %s.', interfaces_to_up)
      self._Dhcpcd(interfaces_to_up, logger)

  def _Dhcpcd(self, interfaces, logger):
    """Use dhcpcd to activate the interfaces.

    Args:
      interfaces: list of string, the output device names to enable.
      logger: logger object, used to write to SysLog and serial port.
    """
    for interface in interfaces:
      dhcpcd = ['/sbin/dhcpcd']
      try:
        subprocess.check_call(dhcpcd + ['-x', interface])
      except subprocess.CalledProcessError:
        # Dhcpcd not yet running for this device.
        logger.info('Dhcpcd not yet running for interface %s.', interface)
      try:
        subprocess.check_call(dhcpcd + [interface])
      except subprocess.CalledProcessError:
        # The interface is already active.
        logger.warning('Could not activate interface %s.', interface)
