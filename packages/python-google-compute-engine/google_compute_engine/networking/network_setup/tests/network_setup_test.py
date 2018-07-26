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

"""Unittest for network_setup.py module."""

import subprocess

from google_compute_engine.networking.network_setup import network_setup
from google_compute_engine.test_compat import mock
from google_compute_engine.test_compat import unittest


class NetworkSetupTest(unittest.TestCase):

  def setUp(self):
    self.mock_logger = mock.Mock()
    self.mock_distro_utils = mock.Mock()
    self.dhclient_script = '/bin/script'
    self.dhcp_command = ''
    self.setup = network_setup.NetworkSetup(
        dhclient_script=self.dhclient_script, dhcp_command=self.dhcp_command,
        debug=False)
    self.setup.distro_utils = self.mock_distro_utils
    self.setup.logger = self.mock_logger

  @mock.patch('google_compute_engine.networking.network_setup.network_setup.subprocess.check_call')
  def testEnableIpv6(self, mock_call):
    mocks = mock.Mock()
    mocks.attach_mock(mock_call, 'call')
    mocks.attach_mock(self.mock_logger, 'logger')
    mocks.attach_mock(self.mock_distro_utils.EnableIpv6, 'enable')
    mock_call.side_effect = [None, subprocess.CalledProcessError(1, 'Test')]

    # Return immediately with no interfaces.
    network_setup.NetworkSetup.EnableIpv6(self.setup, None)
    network_setup.NetworkSetup.EnableIpv6(self.setup, [])
    # Enable interfaces.
    network_setup.NetworkSetup.EnableIpv6(
        self.setup, ['A', 'B'])
    self.assertEqual(self.setup.ipv6_interfaces, set(['A', 'B']))
    # Add a new interface.
    network_setup.NetworkSetup.EnableIpv6(
        self.setup, ['A', 'B', 'C'])
    self.assertEqual(self.setup.ipv6_interfaces, set(['A', 'B', 'C']))
    # Interfaces are already enabled.
    network_setup.NetworkSetup.EnableIpv6(
        self.setup, ['A', 'B', 'C'])
    self.assertEqual(self.setup.ipv6_interfaces, set(['A', 'B', 'C']))
    expected_calls = [
        mock.call.logger.info(mock.ANY, ['A', 'B']),
        mock.call.enable(['A', 'B'], mock.ANY, dhclient_script='/bin/script'),
        mock.call.logger.info(mock.ANY, ['A', 'B', 'C']),
        mock.call.enable(
            ['A', 'B', 'C'], mock.ANY, dhclient_script='/bin/script'),
    ]
    self.assertEqual(mocks.mock_calls, expected_calls)

  @mock.patch('google_compute_engine.networking.network_setup.network_setup.subprocess.check_call')
  def testEnableNetworkInterfaces(self, mock_call):
    mocks = mock.Mock()
    mocks.attach_mock(mock_call, 'call')
    mocks.attach_mock(self.mock_logger, 'logger')
    mocks.attach_mock(self.mock_distro_utils.EnableNetworkInterfaces, 'enable')
    mock_call.side_effect = [None, subprocess.CalledProcessError(1, 'Test')]

    # Return immediately with no interfaces.
    network_setup.NetworkSetup.EnableNetworkInterfaces(self.setup, None)
    network_setup.NetworkSetup.EnableNetworkInterfaces(self.setup, [])
    # Enable interfaces.
    network_setup.NetworkSetup.EnableNetworkInterfaces(
        self.setup, ['A', 'B'])
    self.assertEqual(self.setup.interfaces, set(['A', 'B']))
    # Add a new interface.
    network_setup.NetworkSetup.EnableNetworkInterfaces(
        self.setup, ['A', 'B', 'C'])
    self.assertEqual(self.setup.interfaces, set(['A', 'B', 'C']))
    # Interfaces are already enabled.
    network_setup.NetworkSetup.EnableNetworkInterfaces(
        self.setup, ['A', 'B', 'C'])
    self.assertEqual(self.setup.interfaces, set(['A', 'B', 'C']))
    # Run a user supplied command successfully.
    self.setup.dhcp_command = 'success'
    network_setup.NetworkSetup.EnableNetworkInterfaces(
        self.setup, ['D', 'E'])
    self.assertEqual(self.setup.interfaces, set(['D', 'E']))
    # Run a user supplied command and logger error messages.
    self.setup.dhcp_command = 'failure'
    network_setup.NetworkSetup.EnableNetworkInterfaces(
        self.setup, ['F', 'G'])
    self.assertEqual(self.setup.interfaces, set(['F', 'G']))
    expected_calls = [
        mock.call.logger.info(mock.ANY, ['A', 'B']),
        mock.call.enable(['A', 'B'], mock.ANY, dhclient_script='/bin/script'),
        mock.call.logger.info(mock.ANY, ['A', 'B', 'C']),
        mock.call.enable(
            ['A', 'B', 'C'], mock.ANY, dhclient_script='/bin/script'),
        mock.call.logger.info(mock.ANY, ['D', 'E']),
        mock.call.call(['success']),
        mock.call.logger.info(mock.ANY, ['F', 'G']),
        mock.call.call(['failure']),
        mock.call.logger.warning(mock.ANY),
    ]
    self.assertEqual(mocks.mock_calls, expected_calls)
