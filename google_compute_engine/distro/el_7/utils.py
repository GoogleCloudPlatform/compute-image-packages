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

"""Utilities that are distro specific for use on EL 7."""

import fileinput
import os
import re

from google_compute_engine import constants
from google_compute_engine.distro import helpers
from google_compute_engine.distro import utils


class Utils(utils.Utils):
  """Utilities used by Linux guest services on EL 7."""

  network_path = constants.LOCALBASE + '/etc/sysconfig/network-scripts'

  def EnableNetworkInterfaces(
      self, interfaces, logger, dhclient_script=None):
    """Enable the list of network interfaces.

    Args:
      interfaces: list of string, the output device names to enable.
      logger: logger object, used to write to SysLog and serial port.
      dhclient_script: string, the path to a dhclient script used by dhclient.
    """
    # Should always exist in EL 7.
    if os.path.exists(self.network_path):
      self._DisableNetworkManager(interfaces, logger)
    helpers.CallDhclient(interfaces, logger)

  def _DisableNetworkManager(self, interfaces, logger):
    """Disable network manager management on a list of network interfaces.

    Args:
      interfaces: list of string, the output device names enable.
      logger: logger object, used to write to SysLog and serial port.
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
        logger.info('Created config file for interface %s.', interface)

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
