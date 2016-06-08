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
the IPs configured on eth0, and add or remove addresses from eth0 to make them
match. Only remove those which match our proto code.

Command used to add IPs:
  ip route add to local $IP/32 dev eth0 proto 66
Command used to fetch list of configured IPs:
  ip route ls table local type local dev eth0 scope host proto 66
"""

import logging.handlers
import optparse

from google_compute_engine import config_manager
from google_compute_engine import file_utils
from google_compute_engine import logger
from google_compute_engine import metadata_watcher

from google_compute_engine.ip_forwarding import ip_forwarding_utils

LOCKFILE = '/var/lock/google_ip_forwarding.lock'


class IpForwardingDaemon(object):
  """Manage IP forwarding based on changes to forwarded IPs metadata."""

  forwarded_ips = 'instance/network-interfaces/0/forwarded-ips'

  def __init__(self, proto_id=None, debug=False):
    """Constructor.

    Args:
      proto_id: string, the routing protocol identifier for Google IP changes.
      debug: bool, True if debug output should write to the console.
    """
    facility = logging.handlers.SysLogHandler.LOG_DAEMON
    self.logger = logger.Logger(
        name='google-ip-forwarding', debug=debug, facility=facility)
    self.watcher = metadata_watcher.MetadataWatcher(logger=self.logger)
    self.utils = ip_forwarding_utils.IpForwardingUtils(
        logger=self.logger, proto_id=proto_id)
    try:
      with file_utils.LockFile(LOCKFILE):
        self.logger.info('Starting Google IP Forwarding daemon.')
        self.watcher.WatchMetadata(
            self.HandleForwardedIps, metadata_key=self.forwarded_ips,
            recursive=True)
    except (IOError, OSError) as e:
      self.logger.warning(str(e))

  def _LogForwardedIpChanges(self, configured, desired, to_add, to_remove):
    """Log the planned IP address changes.

    Args:
      configured: list, the IP address strings already configured.
      desired: list, the IP address strings that will be configured.
      to_add: list, the forwarded IP address strings to configure.
      to_remove: list, the forwarded IP address strings to delete.
    """
    if not to_add and not to_remove:
      return
    self.logger.info(
        'Changing forwarded IPs from %s to %s by adding %s and removing %s.',
        configured or None, desired or None, to_add or None, to_remove or None)

  def _AddForwardedIps(self, forwarded_ips):
    """Configure the forwarded IP address on the network interface.

    Args:
      forwarded_ips: list, the forwarded IP address strings to configure.
    """
    for address in forwarded_ips:
      self.utils.AddForwardedIp(address)

  def _RemoveForwardedIps(self, forwarded_ips):
    """Remove the forwarded IP addresses from the network interface.

    Args:
      forwarded_ips: list, the forwarded IP address strings to delete.
    """
    for address in forwarded_ips:
      self.utils.RemoveForwardedIp(address)

  def HandleForwardedIps(self, result):
    """Called when forwarded IPs metadata changes.

    Args:
      result: string, the metadata response with the new forwarded IP addresses.
    """
    desired = self.utils.ParseForwardedIps(result)
    configured = self.utils.GetForwardedIps()
    to_add = sorted(set(desired) - set(configured))
    to_remove = sorted(set(configured) - set(desired))
    self._LogForwardedIpChanges(configured, desired, to_add, to_remove)
    self._AddForwardedIps(to_add)
    self._RemoveForwardedIps(to_remove)


def main():
  parser = optparse.OptionParser()
  parser.add_option('-d', '--debug', action='store_true', dest='debug',
                    help='print debug output to the console.')
  (options, _) = parser.parse_args()
  instance_config = config_manager.ConfigManager()
  if instance_config.GetOptionBool('Daemons', 'ip_forwarding_daemon'):
    IpForwardingDaemon(
        proto_id=instance_config.GetOptionString(
            'IpForwarding', 'ethernet_proto_id'),
        debug=bool(options.debug))


if __name__ == '__main__':
  main()
