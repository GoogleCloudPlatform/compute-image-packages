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


class IpForwardingUtils(object):
  """System IP address configuration utilities."""

  def ParseForwardedIps(self, forwarded_ips):
    """Parse and validate forwarded IP addresses.

    Args:
      forwarded_ips: list, the IP address strings to parse.

    Returns:
      list, the valid IP address strings.
    """
    pass

  def GetForwardedIps(self, interface, interface_ip):
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
