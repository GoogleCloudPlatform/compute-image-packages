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

"""Utilities that are distro specific for use on EL 6."""

from google_compute_engine.distro_lib import helpers
from google_compute_engine.distro_lib import ip_forwarding_utils
from google_compute_engine.distro_lib import utils


class Utils(utils.Utils):
  """Utilities used by Linux guest services on Debian 8."""

  def EnableNetworkInterfaces(
      self, interfaces, logger, dhclient_script=None):
    """Enable the list of network interfaces.

    Args:
      interfaces: list of string, the output device names to enable.
      logger: logger object, used to write to SysLog and serial port.
      dhclient_script: string, the path to a dhclient script used by dhclient.
    """
    helpers.CallDhclient(interfaces, logger, dhclient_script=dhclient_script)

  def HandleClockSync(self, logger):
    """Sync the software clock with the hypervisor clock.

    Args:
      logger: logger object, used to write to SysLog and serial port.
    """
    helpers.CallHwclock(logger)

  def IpForwardingUtils(self, logger, proto_id=None):
    """Get system IP address configuration utilities.

    Args:
      logger: logger object, used to write to SysLog and serial port.
      proto_id: string, the routing protocol identifier for Google IP changes.
    """
    return ip_forwarding_utils.IpForwardingUtilsIproute(logger, proto_id)
