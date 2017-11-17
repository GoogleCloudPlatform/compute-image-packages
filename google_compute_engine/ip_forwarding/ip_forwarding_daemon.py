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

"""Manage IP forwarding on a Google Compute Engine instance.

Fetch a list of public endpoint IPs from the metadata server, compare it with
the IPs configured the associated interfaces, and add or remove addresses from
the interfaces to make them match. Only remove those which match our proto
code.

Command used to add IPs:
  ip route add to local $IP/32 dev eth0 proto 66
Command used to fetch list of configured IPs:
  ip route ls table local type local dev eth0 scope host proto 66
"""

import logging.handlers
import optparse
import random

from google_compute_engine import config_manager
from google_compute_engine import constants
from google_compute_engine import file_utils
from google_compute_engine import logger
from google_compute_engine import metadata_watcher
from google_compute_engine import network_utils
from google_compute_engine.ip_forwarding import ip_forwarding_utils

LOCKFILE = constants.LOCALSTATEDIR + '/lock/google_ip_forwarding.lock'


class IpForwardingDaemon(object):
  """Manage IP forwarding based on changes to forwarded IPs metadata."""

  network_interfaces = 'instance/network-interfaces'

  def __init__(
      self, proto_id=None, ip_aliases=True, target_instance_ips=True,
      debug=False):
    """Constructor.

    Args:
      proto_id: string, the routing protocol identifier for Google IP changes.
      ip_aliases: bool, True if the guest should configure IP alias routes.
      target_instance_ips: bool, True supports internal IP load balancing.
      debug: bool, True if debug output should write to the console.
    """
    facility = logging.handlers.SysLogHandler.LOG_DAEMON
    self.logger = logger.Logger(
        name='google-ip-forwarding', debug=debug, facility=facility)
    self.watcher = metadata_watcher.MetadataWatcher(logger=self.logger)
    self.network_utils = network_utils.NetworkUtils(logger=self.logger)
    self.ip_forwarding_utils = ip_forwarding_utils.IpForwardingUtils(
        logger=self.logger, proto_id=proto_id)
    self.ip_aliases = ip_aliases
    self.target_instance_ips = target_instance_ips
    try:
      with file_utils.LockFile(LOCKFILE):
        self.logger.info('Starting Google IP Forwarding daemon.')
        timeout = 60 + random.randint(0, 30)
        self.watcher.WatchMetadata(
            self.HandleNetworkInterfaces, metadata_key=self.network_interfaces,
            recursive=True, timeout=timeout)
    except (IOError, OSError) as e:
      self.logger.warning(str(e))

  def _LogForwardedIpChanges(
      self, configured, desired, to_add, to_remove, interface):
    """Log the planned IP address changes.

    Args:
      configured: list, the IP address strings already configured.
      desired: list, the IP address strings that will be configured.
      to_add: list, the forwarded IP address strings to configure.
      to_remove: list, the forwarded IP address strings to delete.
      interface: string, the output device to modify.
    """
    if not to_add and not to_remove:
      return
    self.logger.info(
        'Changing %s IPs from %s to %s by adding %s and removing %s.',
        interface, configured or None, desired or None, to_add or None,
        to_remove or None)

  def _AddForwardedIps(self, forwarded_ips, interface):
    """Configure the forwarded IP address on the network interface.

    Args:
      forwarded_ips: list, the forwarded IP address strings to configure.
      interface: string, the output device to use.
    """
    for address in forwarded_ips:
      self.ip_forwarding_utils.AddForwardedIp(address, interface)

  def _RemoveForwardedIps(self, forwarded_ips, interface):
    """Remove the forwarded IP addresses from the network interface.

    Args:
      forwarded_ips: list, the forwarded IP address strings to delete.
      interface: string, the output device to use.
    """
    for address in forwarded_ips:
      self.ip_forwarding_utils.RemoveForwardedIp(address, interface)

  def _HandleForwardedIps(self, forwarded_ips, interface):
    """Handle changes to the forwarded IPs on a network interface.

    Args:
      forwarded_ips: list, the forwarded IP address strings desired.
      interface: string, the output device to configure.
    """
    desired = self.ip_forwarding_utils.ParseForwardedIps(forwarded_ips)
    configured = self.ip_forwarding_utils.GetForwardedIps(interface)
    to_add = sorted(set(desired) - set(configured))
    to_remove = sorted(set(configured) - set(desired))
    self._LogForwardedIpChanges(
        configured, desired, to_add, to_remove, interface)
    self._AddForwardedIps(to_add, interface)
    self._RemoveForwardedIps(to_remove, interface)

  def HandleNetworkInterfaces(self, result):
    """Called when network interface metadata changes.

    Args:
      result: dict, the metadata response with the new network interfaces.
    """
    for network_interface in result:
      mac_address = network_interface.get('mac')
      interface = self.network_utils.GetNetworkInterface(mac_address)
      ip_addresses = []
      if interface:
        ip_addresses.extend(network_interface.get('forwardedIps', []))
        if self.ip_aliases:
          ip_addresses.extend(network_interface.get('ipAliases', []))
        if self.target_instance_ips:
          ip_addresses.extend(network_interface.get('targetInstanceIps', []))
        self._HandleForwardedIps(ip_addresses, interface)
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
  if instance_config.GetOptionBool('Daemons', 'ip_forwarding_daemon'):
    IpForwardingDaemon(
        proto_id=instance_config.GetOptionString(
            'IpForwarding', 'ethernet_proto_id'),
        ip_aliases=instance_config.GetOptionBool(
            'IpForwarding', 'ip_aliases'),
        target_instance_ips=instance_config.GetOptionBool(
            'IpForwarding', 'target_instance_ips'),
        debug=bool(options.debug))


if __name__ == '__main__':
  main()
