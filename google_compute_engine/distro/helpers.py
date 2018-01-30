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

"""Distro helpers."""

import os
import subprocess


def CallDhclient(
    interfaces, logger, dhclient_script=None):
  """Configure the network interfaces using dhclient.

  Args:
    interfaces: list of string, the output device names to enable.
    logger: logger object, used to write to SysLog and serial port.
    dhclient_script: string, the path to a dhclient script used by dhclient.
  """
  logger.info('Enabling the Ethernet interfaces %s.', interfaces)

  dhclient_command = ['dhclient']

  if dhclient_script and os.path.exists(dhclient_script):
    dhclient_command += ['-sf', dhclient_script]

  try:
    subprocess.check_call(dhclient_command + ['-x'] + interfaces)
    subprocess.check_call(dhclient_command + interfaces)
  except subprocess.CalledProcessError:
    logger.warning('Could not enable interfaces %s.', interfaces)
