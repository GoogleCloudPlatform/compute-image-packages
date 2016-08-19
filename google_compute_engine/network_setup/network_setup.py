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

"""Enables the network interfaces provided in metadata."""

import logging.handlers
import optparse
import subprocess

from google_compute_engine import config_manager
from google_compute_engine import logger
from google_compute_engine import metadata_watcher
from google_compute_engine import network_utils


class NetworkSetup(object):
  """Enable network interfaces specified by metadata."""

  network_interfaces = 'instance/network-interfaces'

  def __init__(self, dhcp_binary=None, debug=False):
    """Constructor.

    Args:
      dhcp_binary: string, an executable to enable an ethernet interface.
      debug: bool, True if debug output should write to the console.
    """
    self.dhcp_binary = dhcp_binary or 'dhclient'
    facility = logging.handlers.SysLogHandler.LOG_DAEMON
    self.logger = logger.Logger(
        name='network-setup', debug=debug, facility=facility)
    self.watcher = metadata_watcher.MetadataWatcher(logger=self.logger)
    self.network_utils = network_utils.NetworkUtils(logger=self.logger)
    self._SetupNetworkInterfaces()

  def _EnableNetworkInterface(self, interface):
    """Enable the network interface.

    Args:
      interface: string, the output device to enable.
    """
    if self.network_utils.IsEnabled(interface):
      return

    command = [self.dhcp_binary, interface]
    try:
      self.logger.info('Enabling the ethernet interface %s.', interface)
      subprocess.check_call(command)
    except subprocess.CalledProcessError:
      self.logger.warning('Could not enable the interface %s.', interface)

  def _SetupNetworkInterfaces(self):
    """Get network interfaces metadata and enable each ethernet interface."""
    result = self.watcher.GetMetadata(
        metadata_key=self.network_interfaces, recursive=True)

    for network_interface in result:
      mac_address = network_interface.get('mac')
      interface = self.network_utils.GetNetworkInterface(mac_address)
      if interface:
        self._EnableNetworkInterface(interface)
      else:
        message = 'Network interface not found for MAC address: %s.'
        self.logger.warning(message, mac_address)


def main():
  parser = optparse.OptionParser()
  parser.add_option(
      '-d', '--debug', action='store_true', dest='debug',
      help='print debug output to the console.')
  (options, _) = parser.parse_args()
  instance_config = config_manager.ConfigManager()
  if instance_config.GetOptionBool('NetworkInterfaces', 'setup'):
    NetworkSetup(
        dhcp_binary=instance_config.GetOptionString(
            'NetworkInterfaces', 'dhcp_binary'),
        debug=bool(options.debug))


if __name__ == '__main__':
  main()
