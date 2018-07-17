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

"""Utilities for configuring IP address forwarding."""

import re
import subprocess
try:
  # The following modules are required by IpForwardingUtilsIfconfig.
  import netifaces
  import netaddr
except ImportError:
  netifaces = None
  netaddr = None


IP_REGEX = re.compile(r'\A(\d{1,3}\.){3}\d{1,3}\Z')
IP_ALIAS_REGEX = re.compile(r'\A(\d{1,3}\.){3}\d{1,3}/\d{1,2}\Z')


class IpForwardingUtilsBase(object):
  """System IP address configuration utilities."""

  def ParseForwardedIps(self, forwarded_ips):
    """Parse and validate forwarded IP addresses.

    Args:
      forwarded_ips: list, the IP address strings to parse.

    Returns:
      list, the valid IP address strings.
    """
    pass

  def GetForwardedIps(self, interface, interface_ip=None):
    """Retrieve the list of configured forwarded IP addresses.

    Args:
      interface: string, the output device to query.
      interface_ip: string, current interface ip address.

    Returns:
      list, the IP address strings.
    """
    pass

  def AddForwardedIp(self, address, interface):
    """Configure a new IP address on the network interface.

    Args:
      address: string, the IP address to configure.
      interface: string, the output device to use.
    """
    pass

  def RemoveForwardedIp(self, address, interface):
    """Delete an IP address on the network interface.

    Args:
      address: string, the IP address to configure.
      interface: string, the output device to use.
    """
    pass


class IpForwardingUtilsIproute(IpForwardingUtilsBase):
  """System IP address configuration utilities.

  Command used to add IPs:
    ip route add to local $IP/32 dev eth0 proto 66
  Command used to fetch list of configured IPs:
    ip route ls table local type local dev eth0 scope host proto 66
  """

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

  def GetForwardedIps(self, interface, interface_ip=None):
    """Retrieve the list of configured forwarded IP addresses.

    Args:
      interface: string, the output device to query.
      interface_ip: string, current interface ip address.

    Returns:
      list, the IP address strings.
    """
    args = ['ls', 'table', 'local', 'type', 'local']
    options = self._CreateRouteOptions(dev=interface)
    result = self._RunIpRoute(args=args, options=options)
    result = re.sub(r'local\s', r'', result)
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


class IpForwardingUtilsIfconfig(IpForwardingUtilsBase):
  """System IP address configuration utilities."""

  def __init__(self, logger):
    """Constructor.

    Args:
      logger: logger object, used to write to SysLog and serial port.
    """

    self.logger = logger

  def _RunIfconfig(self, args=None, options=None):
    """Run a command with ifconfig and return the response.

    Args:
      args: list, the string ip route command args to execute.
      options: dict, the string parameters to append to the ip route command.

    Returns:
      string, the standard output from the ip route command execution.
    """
    args = args or []
    options = options or {}
    command = ['ifconfig']
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
        addresses.extend([str(addr) for addr in list(netaddr.IPNetwork(ip))])
      else:
        self.logger.warning('Could not parse IP address: "%s".', ip)
    return addresses

  def GetForwardedIps(self, interface, interface_ip=None):
    """Retrieve the list of configured forwarded IP addresses.

    Args:
      interface: string, the output device to query.
      interface_ip: string, current interface ip address.

    Returns:
      list, the IP address strings.
    """
    try:
      ips = netifaces.ifaddresses(interface)
      ips = ips[netifaces.AF_INET]
    except (ValueError, IndexError):
      return []
    forwarded_ips = []
    for ip in ips:
      if ip['addr'] != interface_ip:
        full_addr = '%s/%d' % (ip['addr'], netaddr.IPAddress(ip['netmask']).netmask_bits())
        forwarded_ips.append(full_addr)
    return self.ParseForwardedIps(forwarded_ips)

  def AddForwardedIp(self, address, interface):
    """Configure a new IP address on the network interface.

    Args:
      address: string, the IP address to configure.
      interface: string, the output device to use.
    """
    for ip in list(netaddr.IPNetwork(address)):
      self._RunIfconfig(args=[interface, 'alias', '%s/32' % str(ip)])

  def RemoveForwardedIp(self, address, interface):
    """Delete an IP address on the network interface.

    Args:
      address: string, the IP address to configure.
      interface: string, the output device to use.
    """
    ip = netaddr.IPNetwork(address)
    self._RunIfconfig(args=[interface, '-alias', str(ip.ip)])
