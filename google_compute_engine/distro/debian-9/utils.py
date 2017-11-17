#!/usr/bin/python
# Copyright 2017 Google Inc. All Rights Reserved.
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

"""Utilities that are distro specific for use on Debian 9."""

import subprocess

from google_compute_engine.distro import utils

class Utils(utils.Utils):
  """Utilities used by Linux guest services on Debian 9."""

  def EnableNetworkInterfaces(self, interfaces, logger=None):
    """Enable the list of network interfaces.

    Args:
      interfaces: list of string, the output device names to enable.
    """
    logger = logger or self.logger
    logger.info('Enabling the Ethernet interfaces %s.', interfaces)
    try:
      subprocess.check_call(['dhclient', '-x'] + interfaces)
      subprocess.check_call(['dhclient'] + interfaces)
    except subprocess.CalledProcessError:
      logger.warning('Could not enable interfaces %s.', interfaces)
