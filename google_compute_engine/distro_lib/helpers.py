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


def CallDhclientIpv6(interfaces, logger, dhclient_script=None):
  """Configure the network interfaces for IPv6 using dhclient.

  Args:
    interface: string, the output device names for enabling IPv6.
    logger: logger object, used to write to SysLog and serial port.
    dhclient_script: string, the path to a dhclient script used by dhclient.
  """
  logger.info('Enabling IPv6 on the Ethernet interfaces %s.', interfaces)

  dhclient_command = ['dhclient']

  if dhclient_script and os.path.exists(dhclient_script):
    dhclient_command += ['-sf', dhclient_script]

  try:
    subprocess.check_call(dhclient_command + ['-1', '-6', '-v'] + interfaces)
  except subprocess.CalledProcessError:
    logger.warning('Could not enable IPv6 on interface %s.', interfaces)


def SetRouteInformationSysctlIPv6(interfaces, logger):
  """Sets accept_ra_rt_info_max_plen on a per interface basis.

  Args:
    interfaces: string, the output device names for enabling Route Advertisements.
    logger: logger object, used to write to SysLog and serial port.
  """
  logger.info('Enabling Route Advertisements on the Ethernet interfaces %s.', interfaces)

  sysctl_command = ['sysctl', '-w']
  for interface in interfaces:
    sysctl_var = ('net.ipv6.conf.{ethinterface}.accept_ra_rt_info_max_plen={value}'.format(
        ethinterface=interface, value=128))
    try:
      subprocess.check_call(sysctl_command + [sysctl_var])
    except subprocess.CalledProcessError:
      logger.warning('Could not enable Route Advertisements on interfaces %s.',
                     interfaces)
  

def CallHwclock(logger):
  """Sync clock using hwclock.

  Args:
    logger: logger object, used to write to SysLog and serial port.
  """
  command = ['/sbin/hwclock', '--hctosys']
  try:
    subprocess.check_call(command)
  except subprocess.CalledProcessError:
    logger.warning('Failed to sync system time with hardware clock.')
  else:
    logger.info('Synced system time with hardware clock.')


def CallNtpdate(logger):
  """Sync clock using ntpdate.

  Args:
    logger: logger object, used to write to SysLog and serial port.
  """
  ntpd_inactive = subprocess.call(['service', 'ntpd', 'status'])
  try:
    if not ntpd_inactive:
      subprocess.check_call(['service', 'ntpd', 'stop'])
    subprocess.check_call(
        'ntpdate `awk \'$1=="server" {print $2}\' /etc/ntp.conf`', shell=True)
    if not ntpd_inactive:
      subprocess.check_call(['service', 'ntpd', 'start'])
  except subprocess.CalledProcessError:
    logger.warning('Failed to sync system time with ntp server.')
  else:
    logger.info('Synced system time with ntp server.')
