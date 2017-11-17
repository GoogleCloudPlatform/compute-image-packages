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

"""Utilities that are distro specific for use on EL 7."""

import subprocess

from google_compute_engine.distro import utils

class Utils(utils.Utils):
  """Utilities used by Linux guest services on EL 7."""

  def EnableNetworkInterfaces(
      self, interfaces, dhclient_script=None, logger=None):
    """Enable the list of network interfaces.

    Args:
      interfaces: list of string, the output device names to enable.
      dhclient_script: string, the path to a dhclient script used by dhclient.
      logger: logger object, used to write to SysLog and serial port.
    """
    logger = logger or self.logger
    logger.info('Enabling the Ethernet interfaces %s.', interfaces)
    try:
      subprocess.check_call(['dhclient', '-x'] + interfaces)
      subprocess.check_call(['dhclient'] + interfaces)
    except subprocess.CalledProcessError:
      logger.warning('Could not enable interfaces %s.', interfaces)

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
