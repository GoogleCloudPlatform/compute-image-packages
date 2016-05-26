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


class IpForwardingUtils(object):
  """System IP address configuration utilities."""

  def __init__(self, logger, proto_id=None):
    """Constructor.

    Args:
      logger: logger object, used to write to SysLog and serial port.
      proto_id: string, the routing protocol identifier for Google IP changes.
    """
    self.logger = logger
    self.options = {
        'dev': self._GetDefaultInterface(),
        'proto': proto_id or '66',
        'scope': 'host',
    }

  def _RunIpRoute(self, args=None, options=None):
    """Run a command with IP route and return the response.

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
        return stdout
    return ''

  def _GetDefaultInterface(self):
    """Get the name of the default network interface.

    Returns:
      string, the name of the default network interface.
    """
    result = self._RunIpRoute(args=['list'])
    for route in result.decode('utf-8').split('\n'):
      fields = route.split()
      if fields and fields[0] == 'default' and 'dev' in fields:
        index = fields.index('dev') + 1
        return fields[index] if index < len(fields) else 'eth0'
    return 'eth0'

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
      if ip and IP_REGEX.match(ip):
        addresses.append(ip)
      else:
        self.logger.warning('Could not parse IP address: "%s".', ip)
    return addresses

  def GetForwardedIps(self):
    """Retrieve the list of configured forwarded IP addresses.

    Returns:
      list, the IP address strings.
    """
    args = ['ls', 'table', 'local', 'type', 'local']
    result = self._RunIpRoute(args=args, options=self.options)
    return self.ParseForwardedIps(result.split())

  def AddForwardedIp(self, address):
    """Configure a new IP address on the network interface.

    Args:
      address: string, the IP address to configure.
    """
    args = ['add', 'to', 'local', '%s/32' % address]
    self._RunIpRoute(args=args, options=self.options)

  def RemoveForwardedIp(self, address):
    """Delete an IP address on the network interface.

    Args:
      address: string, the IP address to configure.
    """
    args = ['delete', 'to', 'local', '%s/32' % address]
    self._RunIpRoute(args=args, options=self.options)
