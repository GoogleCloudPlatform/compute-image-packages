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

"""Utilities for configuring IP address forwarding."""

import re
import subprocess

IP_REGEX = re.compile(r'\A(\d{1,3}\.){3}\d{1,3}\Z')
IP_ALIAS_REGEX = re.compile(r'\A(\d{1,3}\.){3}\d{1,3}/\d{1,2}\Z')


class IpForwardingUtils(object):
  """System IP address configuration utilities."""

  def __init__(self, logger, proto_id=None):
    """Constructor.

    Args:
      logger: logger object, used to write to SysLog and serial port.
      proto_id: string, the routing protocol identifier for Google IP changes.
    """
    self.logger = logger
    self.proto_id = proto_id or '66'

  def _CreateRouteOptions(self, **kwargs):
    """Create a dictionary of parameters to append to the ip route command.

    Args:
      **kwargs: dict, the string parameters to update in the ip route command.

    Returns:
      dict, the string parameters to append to the ip route command.
    """
    options = {
        'proto': self.proto_id,
        'scope': 'host',
    }
    options.update(kwargs)
    return options

  def _RunIpRoute(self, args=None, options=None):
    """Run a command with ip route and return the response.

    Args:
      args: list, the string ip route command args to execute.
      options: dict, the string parameters to append to the ip route command.

    Returns:
      string, the standard output from the ip route command execution.
    """
    args = args or []
    options = options or {}
    command = ['ip', 'route']
    command.extend(args)
    for item in options.items():
      command.extend(item)
    try:
      process = subprocess.Popen(
          command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
      stdout, stderr = process.communicate()
    except OSError as e:
      self.logger.warning('Exception running %s. %s.', command, str(e))
    else:
      if process.returncode:
        message = 'Non-zero exit status running %s. %s.'
        self.logger.warning(message, command, stderr.strip())
      else:
        return stdout.decode('utf-8', 'replace')
    return ''

  def ParseForwardedIps(self, forwarded_ips):
    """Parse and validate forwarded IP addresses.

    Args:
      forwarded_ips: list, the IP address strings to parse.

    Returns:
      list, the valid IP address strings.
    """
    addresses = []
    forwarded_ips = forwarded_ips or []
    for ip in forwarded_ips:
      if ip and (IP_REGEX.match(ip) or IP_ALIAS_REGEX.match(ip)):
        addresses.append(ip[:-3] if ip.endswith('/32') else ip)
      else:
        self.logger.warning('Could not parse IP address: "%s".', ip)
    return addresses

  def GetForwardedIps(self, interface):
    """Retrieve the list of configured forwarded IP addresses.

    Args:
      interface: string, the output device to query.

    Returns:
      list, the IP address strings.
    """
    args = ['ls', 'table', 'local', 'type', 'local']
    options = self._CreateRouteOptions(dev=interface)
    result = self._RunIpRoute(args=args, options=options)
    return self.ParseForwardedIps(result.split())

  def AddForwardedIp(self, address, interface):
    """Configure a new IP address on the network interface.

    Args:
      address: string, the IP address to configure.
      interface: string, the output device to use.
    """
    address = address if IP_ALIAS_REGEX.match(address) else '%s/32' % address
    args = ['add', 'to', 'local', address]
    options = self._CreateRouteOptions(dev=interface)
    self._RunIpRoute(args=args, options=options)

  def RemoveForwardedIp(self, address, interface):
    """Delete an IP address on the network interface.

    Args:
      address: string, the IP address to configure.
      interface: string, the output device to use.
    """
    address = address if IP_ALIAS_REGEX.match(address) else '%s/32' % address
    args = ['delete', 'to', 'local', address]
    options = self._CreateRouteOptions(dev=interface)
    self._RunIpRoute(args=args, options=options)
