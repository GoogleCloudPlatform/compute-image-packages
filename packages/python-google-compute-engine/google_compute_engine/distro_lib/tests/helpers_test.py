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

"""Unittest for helpers.py module."""

import subprocess

from google_compute_engine.distro_lib import helpers
from google_compute_engine.test_compat import mock
from google_compute_engine.test_compat import unittest


class HelpersTest(unittest.TestCase):

  def setUp(self):
    self.mock_logger = mock.Mock()

  @mock.patch('google_compute_engine.distro_lib.helpers.os.path.exists')
  @mock.patch('google_compute_engine.distro_lib.helpers.subprocess.check_call')
  def testCallDhclient(self, mock_call, mock_exists):
    mocks = mock.Mock()
    mocks.attach_mock(mock_exists, 'exists')
    mocks.attach_mock(mock_call, 'call')
    mocks.attach_mock(self.mock_logger, 'logger')

    mock_exists.side_effect = [False, True]
    mock_call.side_effect = [
        None, None, None, None, None, None,
        subprocess.CalledProcessError(1, 'Test'),
    ]

    helpers.CallDhclient(['a', 'b'], self.mock_logger, 'test_script')
    helpers.CallDhclient(['c', 'd'], self.mock_logger, 'test_script')
    helpers.CallDhclient(['e', 'f'], self.mock_logger, None)
    helpers.CallDhclient(['g', 'h'], self.mock_logger, None)

    expected_calls = [
        mock.call.logger.info(mock.ANY, ['a', 'b']),
        mock.call.exists('test_script'),
        mock.call.call(['dhclient', '-x', 'a', 'b']),
        mock.call.call(['dhclient', 'a', 'b']),
        mock.call.logger.info(mock.ANY, ['c', 'd']),
        mock.call.exists('test_script'),
        mock.call.call(['dhclient', '-sf', 'test_script', '-x', 'c', 'd']),
        mock.call.call(['dhclient', '-sf', 'test_script', 'c', 'd']),
        mock.call.logger.info(mock.ANY, ['e', 'f']),
        mock.call.call(['dhclient', '-x', 'e', 'f']),
        mock.call.call(['dhclient', 'e', 'f']),
        mock.call.logger.info(mock.ANY, ['g', 'h']),
        mock.call.call(['dhclient', '-x', 'g', 'h']),
        mock.call.logger.warning(mock.ANY, ['g', 'h']),
    ]

    self.assertEqual(mocks.mock_calls, expected_calls)

  @mock.patch('google_compute_engine.distro_lib.helpers.os.path.exists')
  @mock.patch('google_compute_engine.distro_lib.helpers.subprocess.check_call')
  def testCallDhclientIpv6NonExistentScript(self, mock_call, mock_exists):
    mock_logger = mock.Mock()

    mock_exists.side_effect = [False]
    helpers.CallDhclientIpv6(['a', 'b'], mock_logger, 'test_script')
    mock_call.assert_has_calls(
        [
            mock.call.call(
                ['timeout', '5', 'dhclient', '-1', '-6', '-v', 'a', 'b']),
        ])

  @mock.patch('google_compute_engine.distro_lib.helpers.os.path.exists')
  @mock.patch('google_compute_engine.distro_lib.helpers.subprocess.check_call')
  def testCallDhclientIpv6(self, mock_call, mock_exists):
    mock_logger = mock.Mock()
    mock_exists.side_effect = [True]
    mock_call.side_effect = [
        None,
        None,
        subprocess.CalledProcessError(1, 'Test'),
        None,
        None,
        subprocess.CalledProcessError(1, 'Test'),
    ]

    helpers.CallDhclientIpv6(['a', 'b'], mock_logger, 'test_script')
    helpers.CallDhclientIpv6(['c', 'd'], mock_logger, None)
    helpers.CallDhclientIpv6(['e', 'f'], mock_logger, None)
    helpers.CallDhclientIpv6(
        ['g', 'h'], mock_logger, 'test_script', release_lease=True)
    helpers.CallDhclientIpv6(['i', 'j'], mock_logger, None, release_lease=True)
    helpers.CallDhclientIpv6(['k', 'l'], mock_logger, None, release_lease=True)

    expected_calls = [
        mock.call.call(
            [
                'timeout', '5','dhclient', '-sf', 'test_script', '-1', '-6',
                '-v', 'a', 'b',
            ]),
        mock.call.call(
            [
                'timeout', '5', 'dhclient', '-1', '-6', '-v', 'c', 'd',
            ]),
        mock.call.call(
            [
                'timeout', '5', 'dhclient', '-1', '-6', '-v', 'e', 'f',
             ]),
        mock.call.call(
            [
                'timeout', '5', 'dhclient', '-6', '-r', '-v', 'g', 'h',
            ]),
        mock.call.call(
            [
                'timeout', '5', 'dhclient', '-6', '-r', '-v', 'i', 'j',
            ]),
        mock.call.call(
            [
                'timeout', '5', 'dhclient', '-6', '-r', '-v', 'k', 'l',
            ]),
    ]

    self.assertEqual(mock_call.mock_calls, expected_calls)
    mock_logger.assert_has_calls(
        [
            mock.call.warning(mock.ANY, ['e', 'f']),
        ])
    mock_logger.assert_has_calls(
        [
            mock.call.warning(mock.ANY, ['k', 'l']),
        ])

  @mock.patch('google_compute_engine.distro_lib.helpers.subprocess.check_call')
  def testEnableRouteAdvertisements(self, mock_call):
    mock_logger = mock.Mock()
    interfaces = ['foo', 'bar', 'baz']
    helpers.CallEnableRouteAdvertisements(interfaces, mock_logger)
    mock_call.assert_has_calls([
        mock.call(
            [
                'sysctl', '-w',
                'net.ipv6.conf.%s.accept_ra_rt_info_max_plen=128' % interface,
            ])
        for interface in interfaces])

  @mock.patch('google_compute_engine.distro_lib.helpers.subprocess.check_call')
  def testCallHwclock(self, mock_call):
    command = ['/sbin/hwclock', '--hctosys']
    mock_logger = mock.Mock()

    helpers.CallHwclock(mock_logger)
    mock_call.assert_called_once_with(command)
    expected_calls = [mock.call.info(mock.ANY)]
    self.assertEqual(mock_logger.mock_calls, expected_calls)

  @mock.patch('google_compute_engine.distro_lib.helpers.subprocess.check_call')
  def testCallHwclockError(self, mock_call):
    command = ['/sbin/hwclock', '--hctosys']
    mock_logger = mock.Mock()
    mock_call.side_effect = subprocess.CalledProcessError(1, 'Test')

    helpers.CallHwclock(mock_logger)
    mock_call.assert_called_once_with(command)
    expected_calls = [mock.call.warning(mock.ANY)]
    self.assertEqual(mock_logger.mock_calls, expected_calls)

  @mock.patch('google_compute_engine.distro_lib.helpers.subprocess.check_call')
  @mock.patch('google_compute_engine.distro_lib.helpers.subprocess.call')
  def testCallNtpdateActive(self, mock_call, mock_check_call):
    command_status = ['service', 'ntpd', 'status']
    command_stop = ['service', 'ntpd', 'stop']
    command_start = ['service', 'ntpd', 'start']
    command_ntpdate = 'ntpdate `awk \'$1=="server" {print $2}\' /etc/ntp.conf`'
    mock_logger = mock.Mock()
    mock_call.return_value = 0
    mock_check_call.return_value = True

    helpers.CallNtpdate(mock_logger)
    mock_call.assert_called_once_with(command_status)
    expected_calls = [
        mock.call(command_stop),
        mock.call(command_ntpdate, shell=True),
        mock.call(command_start),
    ]
    self.assertEqual(mock_check_call.mock_calls, expected_calls)
    expected_calls = [mock.call.info(mock.ANY)]
    self.assertEqual(mock_logger.mock_calls, expected_calls)

  @mock.patch('google_compute_engine.distro_lib.helpers.subprocess.check_call')
  @mock.patch('google_compute_engine.distro_lib.helpers.subprocess.call')
  def testCallNtpdateInactive(self, mock_call, mock_check_call):
    command_status = ['service', 'ntpd', 'status']
    command_ntpdate = 'ntpdate `awk \'$1=="server" {print $2}\' /etc/ntp.conf`'
    mock_logger = mock.Mock()
    mock_call.return_value = 1

    helpers.CallNtpdate(mock_logger)
    mock_call.assert_called_once_with(command_status)
    mock_check_call.assert_called_once_with(command_ntpdate, shell=True)
    expected_calls = [mock.call.info(mock.ANY)]
    self.assertEqual(mock_logger.mock_calls, expected_calls)

  @mock.patch('google_compute_engine.distro_lib.helpers.subprocess.check_call')
  @mock.patch('google_compute_engine.distro_lib.helpers.subprocess.call')
  def testCallNtpdateError(self, mock_call, mock_check_call):
    command_status = ['service', 'ntpd', 'status']
    command_ntpdate = 'ntpdate `awk \'$1=="server" {print $2}\' /etc/ntp.conf`'
    mock_logger = mock.Mock()
    mock_check_call.side_effect = subprocess.CalledProcessError(1, 'Test')

    helpers.CallNtpdate(mock_logger)
    mock_call.assert_called_once_with(command_status)
    mock_check_call.assert_called_once_with(command_ntpdate, shell=True)
    expected_calls = [mock.call.warning(mock.ANY)]
    self.assertEqual(mock_logger.mock_calls, expected_calls)

  @mock.patch('google_compute_engine.distro_lib.helpers.subprocess.check_call')
  def testCallSysctl(self, mock_call):
    command = ['sysctl', '-w']
    mock_logger = mock.Mock()
    expected_log_calls = []
    for name in ['foo', 'bar', 'baz']:
      for value in ['foo', 'bar', 'baz']:
        params = ['{name}={value}'.format(name=name, value=value)]
        helpers.CallSysctl(mock_logger, name, value)
        mock_call.assert_called_with(command + params)
        expected_log_calls.append(mock.call.info(mock.ANY, name))
    self.assertEqual(mock_logger.mock_calls, expected_log_calls)

    mock_call.side_effect = subprocess.CalledProcessError(1, 'Test')
    helpers.CallSysctl(mock_logger, 'fail', 1)
    mock_logger.assert_has_calls([mock.call.warning(mock.ANY, 'fail')])
