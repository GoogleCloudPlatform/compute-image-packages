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

"""Utilities that are distro specific."""

import logging.handlers

from google_compute_engine import logger as loggger
from google_compute_engine import network_utils


class Utils(object):
  """Utilities used by Linux guest services."""

  def __init__(self, debug=False, logger=None):
    """Constructor.

    Args:
      debug: bool, True if debug output should write to the console.
      logger: logger object, used to write to SysLog and serial port.
    """
    self.debug = debug
    facility = logging.handlers.SysLogHandler.LOG_DAEMON
    self.logger = logger or loggger.Logger(
        name='google-utils', debug=self.debug, facility=facility)
    self.network_utils = network_utils.NetworkUtils(logger=self.logger)

  def EnableNetworkInterfaces(
      self, interfaces, dhclient_script=None, logger=None):
    """Enable the list of network interfaces.

    Args:
      interfaces: list of string, the output device names to enable.
      dhclient_script: string, the path to a dhclient script used by dhclient.
      logger: logger object, used to write to SysLog and serial port.
    """
    pass
