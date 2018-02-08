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

"""Refresh dhcp for interfaces as controlled my metadata."""

import logging.handlers

from google_compute_engine import logger
from google_compute_engine.compat import distro_utils


class DhcpRefresh(object):
  """Refreshes dhcp."""

  def __init__(self, dhcpv6_tokens, debug=False):
    """Constructor.

    Args:
      dhcpv6_tokens: dict, initial state of interfaces at startup.
      debug: bool, True if debug output should write to the console.
    """
    facility = logging.handlers.SysLogHandler.LOG_DAEMON
    self.logger = logger.Logger(
        name='dhcp-refresh', debug=debug, facility=facility)
    self.distro_utils = distro_utils.Utils(debug=debug)
    self.dhcpv6_tokens = dhcpv6_tokens

  def RefreshDhcp(self, interface, dhcpv6_refresh_token):
    """Refresh dhcp for the interface if the token has changed.

    Args:
      interface: string, the output device to refresh.
      dhcpv6_refresh_token: string, the dhcpv6 refresh token from the metadata.
    """
    if self.dhcpv6_tokens.get(interface) is not dhcpv6_refresh_token:
      self.dhcpv6_tokens[interface] = dhcpv6_refresh_token
      self.distro_utils.RefreshDhcpV6(interface)
