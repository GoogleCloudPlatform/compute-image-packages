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
import time


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


def CallDhclientIpv6(interfaces, logger, dhclient_script=None,
                     release_lease=False):
  """Configure the network interfaces for IPv6 using dhclient.

  Args:
    interface: string, the output device names for enabling IPv6.
    logger: logger object, used to write to SysLog and serial port.
    dhclient_script: string, the path to a dhclient script used by dhclient.
    release_lease: Release the IPv6 lease.
  """
  logger.info('Calling Dhclient for IPv6 configuration '
              'on the Ethernet interfaces %s.', interfaces)

  timeout_command = ['timeout', '5']
  dhclient_command = ['dhclient']

  if release_lease:
    try:
      subprocess.check_call(
          timeout_command + dhclient_command + [
              '-6', '-r', '-v'] + interfaces)
    except subprocess.CalledProcessError:
      logger.warning('Could not release IPv6 lease on interface %s.',
                     interfaces)
    return

  # Check for a 'tentative' IPv6 address which would prevent `dhclient -6` from
  # succeeding below. This should only take 1 second, but we try for up to 5.
  command = ['ip', '-6', '-o', 'a', 's', 'dev', interfaces[0], 'scope',
             'link', 'tentative']
  for i in range(5):
    output = ''
    try:
      output = subprocess.check_output(command)
    except subprocess.CalledProcessError as e:
      logger.warning('Could not confirm tentative IPv6 address: %s.', e.output)
    if output:
      logger.info('Found tentative ipv6 link address %s, sleeping 1 second.',
                  output.strip())
      time.sleep(1)
    else:
      break

  if dhclient_script and os.path.exists(dhclient_script):
    dhclient_command += ['-sf', dhclient_script]

  try:
    subprocess.check_call(
        timeout_command + dhclient_command + ['-1', '-6', '-v'] + interfaces)
  except subprocess.CalledProcessError:
    logger.warning('Could not enable IPv6 on interface %s.', interfaces)


def CallEnableRouteAdvertisements(interfaces, logger):
  """Enable route advertisements.

  Args:
    interfaces: list of string, the output device names to enable.
    logger: logger object, used to write to SysLog and serial port.
  """
  for interface in interfaces:
    accept_ra = (
        'net.ipv6.conf.{interface}.accept_ra_rt_info_max_plen'.format(
            interface=interface))
    CallSysctl(logger, accept_ra, 128)

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

def CallSysctl(logger, name, value):
  """Write a variable using sysctl.

  Args:
      logger: logger object, used to write to SysLog and serial port.
      name: string name of the sysctl variable.
      value: value of the sysctl variable.
  """
  logger.info('Configuring sysctl %s.', name)

  sysctl_command = [
      'sysctl', '-w', '{name}={value}'.format(name=name, value=value)]
  try:
    subprocess.check_call(sysctl_command)
  except subprocess.CalledProcessError:
    logger.warning('Unable to configure sysctl %s.', name)

def SystemctlRestart(service, logger):
  """Restart a service using systemctl.

  Args:
      service: the name of the service to restart.
      logger: logger object, used to write to SysLog and serial port.
  """
  logger.info('Restarting service via "systemctl restart %s".', service)
  systemctl_command = ['systemctl', 'restart', service]
  try:
    subprocess.check_call(systemctl_command)
  except subprocess.CalledProcessError:
    logger.warning('Failed to restart service %s.', service)
