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

"""Enables the network interfaces for multi-nic support."""

import logging.handlers
import subprocess

from google_compute_engine import logger
from google_compute_engine.compat import distro_utils


class NetworkSetup(object):
  """Enable network interfaces."""

  interfaces = set()
  network_interfaces = 'instance/network-interfaces'

  def __init__(self, dhclient_script=None, dhcp_command=None, debug=False):
    """Constructor.

    Args:
      dhclient_script: string, the path to a dhclient script used by dhclient.
      dhcp_command: string, a command to enable Ethernet interfaces.
      debug: bool, True if debug output should write to the console.
    """
    self.dhclient_script = dhclient_script or '/sbin/google-dhclient-script'
    self.dhcp_command = dhcp_command
    facility = logging.handlers.SysLogHandler.LOG_DAEMON
    self.logger = logger.Logger(
        name='network-setup', debug=debug, facility=facility)
    self.distro_utils = distro_utils.Utils(debug=debug)

  def EnableNetworkInterfaces(self, interfaces):
    """Enable the list of network interfaces.

    Args:
      interfaces: list of string, the output device names to enable.
    """
    # The default Ethernet interface is enabled by default. Do not attempt to
    # enable interfaces if only one interface is specified in metadata.
    if not interfaces or set(interfaces) == self.interfaces:
      return

    self.logger.info('Ethernet interfaces: %s.', interfaces)
    self.interfaces = set(interfaces)
    if len(interfaces) <= 1:
      return

    if self.dhcp_command:
      try:
        subprocess.check_call([self.dhcp_command])
      except subprocess.CalledProcessError:
        self.logger.warning('Could not enable Ethernet interfaces.')
      return

    # Distro-specific setup for network interfaces.
    self.distro_utils.EnableNetworkInterfaces(
        interfaces, self.logger, dhclient_script=self.dhclient_script)
