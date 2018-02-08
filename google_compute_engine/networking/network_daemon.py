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

"""Manage networking on a Google Compute Engine instance.

Run network setup to enable multiple network interfaces on startup.
Update IP forwarding when metadata changes.
Refresh dhcp when metadata refresh token changes.
"""

import logging.handlers
import optparse
import random

from google_compute_engine import config_manager
from google_compute_engine import constants
from google_compute_engine import file_utils
from google_compute_engine import logger
from google_compute_engine import metadata_watcher
from google_compute_engine.networking import dhcp_refresh
from google_compute_engine.networking import ip_forwarding
from google_compute_engine.networking import network_setup
from google_compute_engine.networking import network_utils

LOCKFILE = constants.LOCALSTATEDIR + '/lock/google_networking.lock'


class NetworkDaemon(object):
  """Manage networking based on changes to network metadata."""

  network_interfaces = 'instance/network-interfaces'

  def __init__(
      self, ip_forwarding_enabled, proto_id, ip_aliases, target_instance_ips,
      dhclient_script, dhcp_command, dhcp_refresh_enabled,
      network_setup_enabled, debug=False):
    """Constructor.

    Args:
      ip_forwarding_enabled: bool, True if ip forwarding is enabled.
      proto_id: string, the routing protocol identifier for Google IP changes.
      ip_aliases: bool, True if the guest should configure IP alias routes.
      target_instance_ips: bool, True supports internal IP load balancing.
      dhclient_script: string, the path to a dhclient script used by dhclient.
      dhcp_command: string, a command to enable Ethernet interfaces.
      dhcp_refresh_enabled: bool, True if dhcp refresh is enabled.
      network_setup_enabled: bool, True if network setup is enabled.
      debug: bool, True if debug output should write to the console.
    """
    facility = logging.handlers.SysLogHandler.LOG_DAEMON
    self.logger = logger.Logger(
        name='google-networking', debug=debug, facility=facility)
    self.network_utils = network_utils.NetworkUtils(logger=self.logger)
    self.watcher = metadata_watcher.MetadataWatcher(logger=self.logger)

    self.ip_aliases = ip_aliases
    self.target_instance_ips = target_instance_ips

    # Get initial metadata.
    result = self.watcher.GetMetadata(
        metadata_key=self.network_interfaces, recursive=True)
    interface_details = self._ExtractInterfaceMetadata(result)

    if network_setup_enabled:
      interfaces = [interface for interface, _, _ in interface_details]
      network_setup.NetworkSetup(
          interfaces, dhclient_script=dhclient_script,
          dhcp_command=dhcp_command, debug=debug)

    self.ip_forwarding_enabled = ip_forwarding_enabled
    if ip_forwarding_enabled:
      self.ip_forwarding = ip_forwarding.IpForwarding(proto_id, debug)

    self.dhcp_refresh_enabled = dhcp_refresh_enabled
    if dhcp_refresh_enabled:
      dhcpv6_tokens = {name: dhcpv6_token
          for name, _, dhcpv6_token in interface_details}
      self.dhcp_refresh = dhcp_refresh.DhcpRefresh(dhcpv6_tokens, debug)

    try:
      with file_utils.LockFile(LOCKFILE):
        self.logger.info('Starting Google Networking daemon.')
        timeout = 60 + random.randint(0, 30)
        self.watcher.WatchMetadata(
            self.HandleNetworkInterfaces, metadata_key=self.network_interfaces,
            recursive=True, timeout=timeout)
    except (IOError, OSError) as e:
      self.logger.warning(str(e))

  def HandleNetworkInterfaces(self, result):
    """Called when network interface metadata changes.

    Args:
      result: dict, the metadata response with the network interfaces.
    """
    interface_details = self._ExtractInterfaceMetadata(result)

    for interface, forwarded_ips, dhcpv6_refresh_token in interface_details:
      if self.ip_forwarding_enabled:
        self.ip_forwarding.HandleForwardedIps(interface, forwarded_ips)
      if self.dhcp_refresh_enabled:
        self.dhcp_refresh.RefreshDhcp(interface, dhcpv6_refresh_token)

  def _ExtractInterfaceMetadata(self, metadata):
    """Extracts network interface metadata.

    Args:
      metadata: dict, the metadata response with the new network interfaces.

    Returns:
      list, the network output device information.
    """
    interfaces = []
    for network_interface in metadata:
      mac_address = network_interface.get('mac')
      interface = self.network_utils.GetNetworkInterface(mac_address)
      ip_addresses = []
      if interface:
        dhcpv6_refresh_token = network_interface.get('dhcpv6-refresh')
        ip_addresses.extend(network_interface.get('forwardedIps', []))
        if self.ip_aliases:
          ip_addresses.extend(network_interface.get('ipAliases', []))
        if self.target_instance_ips:
          ip_addresses.extend(network_interface.get('targetInstanceIps', []))
        interfaces.append((interface, ip_addresses, dhcpv6_refresh_token))
      else:
        message = 'Network interface not found for MAC address: %s.'
        self.logger.warning(message, mac_address)
    return interfaces


def main():
  parser = optparse.OptionParser()
  parser.add_option(
      '-d', '--debug', action='store_true', dest='debug',
      help='print debug output to the console.')
  (options, _) = parser.parse_args()
  debug = bool(options.debug)
  instance_config = config_manager.ConfigManager()
  ip_forwarding_daemon_enabled = instance_config.GetOptionBool(
      'Daemons', 'ip_forwarding_daemon')
  ip_forwarding_enabled = instance_config.GetOptionBool(
      'NetworkInterfaces', 'ip_forwarding') or ip_forwarding_daemon_enabled
  network_setup_enabled = instance_config.GetOptionBool(
      'NetworkInterfaces', 'setup')
  dhcp_refresh_enabled = instance_config.GetOptionBool(
      'NetworkInterfaces', 'dhcp_refresh')
  network_daemon_enabled = instance_config.GetOptionBool(
      'Daemons', 'network_daemon')
  proto_id = instance_config.GetOptionString(
      'IpForwarding', 'ethernet_proto_id')
  ip_aliases = instance_config.GetOptionBool(
      'IpForwarding', 'ip_aliases')
  target_instance_ips = instance_config.GetOptionBool(
      'IpForwarding', 'target_instance_ips')
  dhclient_script = instance_config.GetOptionString(
      'NetworkInterfaces', 'dhclient_script')
  dhcp_command = instance_config.GetOptionString(
      'NetworkInterfaces', 'dhcp_command')

  if network_daemon_enabled:
    NetworkDaemon(
        ip_forwarding_enabled=ip_forwarding_enabled,
        proto_id=proto_id,
        ip_aliases=ip_aliases,
        target_instance_ips=target_instance_ips,
        dhclient_script=dhclient_script,
        dhcp_command=dhcp_command,
        dhcp_refresh_enabled=dhcp_refresh_enabled,
        network_setup_enabled=network_setup_enabled,
        debug=debug)


if __name__ == '__main__':
  main()
