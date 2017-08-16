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

import fileinput
import logging.handlers
import optparse
import os
import re
import subprocess

from google_compute_engine import config_manager
from google_compute_engine import constants
from google_compute_engine import logger
from google_compute_engine import metadata_watcher
from google_compute_engine import network_utils


class NetworkSetup(object):
  """Enable network interfaces specified by metadata."""

  network_interfaces = 'instance/network-interfaces'
  network_path = constants.LOCALBASE + '/etc/sysconfig/network-scripts'

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
    self.watcher = metadata_watcher.MetadataWatcher(logger=self.logger)
    self.network_utils = network_utils.NetworkUtils(logger=self.logger)
    self._SetupNetworkInterfaces()

  def _ModifyInterface(
      self, interface_config, config_key, config_value, replace=False):
    """Write a value to a config file if not already present.

    Args:
      interface_config: string, the path to a config file.
      config_key: string, the configuration key to set.
      config_value: string, the value to set for the configuration key.
      replace: bool, replace the configuration option if already present.
    """
    config_entry = '%s=%s' % (config_key, config_value)
    if not open(interface_config).read().count(config_key):
      with open(interface_config, 'a') as config:
        config.write('%s\n' % config_entry)
    elif replace:
      for line in fileinput.input(interface_config, inplace=True):
        print(re.sub(r'%s=.*' % config_key, config_entry, line.rstrip()))

  def _DisableNetworkManager(self, interfaces):
    """Disable network manager management on a list of network interfaces.

    Args:
      interfaces: list of string, the output device names enable.
    """
    for interface in interfaces:
      interface_config = os.path.join(self.network_path, 'ifcfg-%s' % interface)
      if os.path.exists(interface_config):
        self._ModifyInterface(
            interface_config, 'DEVICE', interface, replace=False)
        self._ModifyInterface(
            interface_config, 'NM_CONTROLLED', 'no', replace=True)
      else:
        with open(interface_config, 'w') as interface_file:
          interface_content = [
              '# Added by Google.',
              'BOOTPROTO=none',
              'DEFROUTE=no',
              'DEVICE=%s' % interface,
              'IPV6INIT=no',
              'NM_CONTROLLED=no',
              'NOZEROCONF=yes',
              '',
          ]
          interface_file.write('\n'.join(interface_content))
        self.logger.info('Created config file for interface %s.', interface)

  def _ConfigureNetwork(self, interfaces):
    """Enable the list of network interfaces.

    Args:
      interfaces: list of string, the output device names enable.
    """
    self.logger.info('Enabling the Ethernet interfaces %s.', interfaces)
    dhclient_command = ['dhclient']
    if os.path.exists(self.dhclient_script):
      dhclient_command += ['-sf', self.dhclient_script]
    try:
      subprocess.check_call(dhclient_command + ['-x'] + interfaces)
      subprocess.check_call(dhclient_command + interfaces)
    except subprocess.CalledProcessError:
      self.logger.warning('Could not enable interfaces %s.', interfaces)

  def _EnableNetworkInterfaces(self, interfaces):
    """Enable the list of network interfaces.

    Args:
      interfaces: list of string, the output device names to enable.
    """
    # The default Ethernet interface is enabled by default. Do not attempt to
    # enable interfaces if only one interface is specified in metadata.
    if not interfaces or len(interfaces) <= 1:
      return

    if self.dhcp_command:
      try:
        subprocess.check_call([self.dhcp_command])
      except subprocess.CalledProcessError:
        self.logger.warning('Could not enable Ethernet interfaces.')
    else:
      if os.path.exists(self.network_path):
        self._DisableNetworkManager(interfaces)
      self._ConfigureNetwork(interfaces)

  def _SetupNetworkInterfaces(self):
    """Get network interfaces metadata and enable each Ethernet interface."""
    result = self.watcher.GetMetadata(
        metadata_key=self.network_interfaces, recursive=True)
    interfaces = []

    for network_interface in result:
      mac_address = network_interface.get('mac')
      interface = self.network_utils.GetNetworkInterface(mac_address)
      if interface:
        interfaces.append(interface)
      else:
        message = 'Network interface not found for MAC address: %s.'
        self.logger.warning(message, mac_address)

    self._EnableNetworkInterfaces(interfaces)


def main():
  parser = optparse.OptionParser()
  parser.add_option(
      '-d', '--debug', action='store_true', dest='debug',
      help='print debug output to the console.')
  (options, _) = parser.parse_args()
  instance_config = config_manager.ConfigManager()
  if instance_config.GetOptionBool('NetworkInterfaces', 'setup'):
    NetworkSetup(
        dhclient_script=instance_config.GetOptionString(
            'NetworkInterfaces', 'dhclient_script'),
        dhcp_command=instance_config.GetOptionString(
            'NetworkInterfaces', 'dhcp_command'),
        debug=bool(options.debug))


if __name__ == '__main__':
  main()
