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

When given a list of public endpoint IPs, compare it with the IPs configured
for the associated interfaces, and add or remove addresses from the interfaces
to make them match. Only remove those which match our proto code.

Command used to add IPs:
  ip route add to local $IP/32 dev eth0 proto 66
Command used to fetch list of configured IPs:
  ip route ls table local type local dev eth0 scope host proto 66
"""

import logging.handlers

from google_compute_engine import logger
from google_compute_engine.networking.ip_forwarding import ip_forwarding_utils


class IpForwarding(object):
  """Manage IP forwarding based on changes to forwarded IPs metadata."""

  def __init__(self, proto_id=None, debug=False):
    """Constructor.

    Args:
      proto_id: string, the routing protocol identifier for Google IP changes.
      debug: bool, True if debug output should write to the console.
    """
    facility = logging.handlers.SysLogHandler.LOG_DAEMON
    self.logger = logger.Logger(
        name='google-ip-forwarding', debug=debug, facility=facility)
    self.ip_forwarding_utils = ip_forwarding_utils.IpForwardingUtils(
        logger=self.logger, proto_id=proto_id)

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

  def HandleForwardedIps(self, interface, forwarded_ips):
    """Handle changes to the forwarded IPs on a network interface.

    Args:
      interface: string, the output device to configure.
      forwarded_ips: list, the forwarded IP address strings desired.
    """
    desired = self.ip_forwarding_utils.ParseForwardedIps(forwarded_ips)
    configured = self.ip_forwarding_utils.GetForwardedIps(interface)
    to_add = sorted(set(desired) - set(configured))
    to_remove = sorted(set(configured) - set(desired))
    self._LogForwardedIpChanges(
        configured, desired, to_add, to_remove, interface)
    self._AddForwardedIps(to_add, interface)
    self._RemoveForwardedIps(to_remove, interface)
