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
    self.mock_setup = mock.create_autospec(network_setup.NetworkSetup)
    self.mock_setup.logger = self.mock_logger
    self.mock_setup.distro_utils = self.mock_distro_utils
    self.mock_setup.dhclient_script = '/bin/script'
    self.mock_setup.dhcp_command = ''

  @mock.patch('google_compute_engine.networking.network_setup.network_setup.logger')
  def testNetworkSetup(self, mock_logger):
    mock_logger_instance = mock.Mock()
    mock_logger.Logger.return_value = mock_logger_instance
    mocks = mock.Mock()
    mocks.attach_mock(mock_logger, 'logger')
    with mock.patch.object(
        network_setup.NetworkSetup, 'EnableNetworkInterfaces'):

      network_setup.NetworkSetup(['A', 'B'], debug=True)
      expected_calls = [
          mock.call.logger.Logger(name=mock.ANY, debug=True, facility=mock.ANY),
      ]
      self.assertEqual(mocks.mock_calls, expected_calls)

  @mock.patch('google_compute_engine.networking.network_setup.network_setup.subprocess.check_call')
  def testEnableNetworkInterfaces(self, mock_call):
    mocks = mock.Mock()
    mocks.attach_mock(mock_call, 'call')
    mocks.attach_mock(self.mock_logger, 'logger')
    mocks.attach_mock(
        self.mock_setup.distro_utils.EnableNetworkInterfaces, 'enable')
    mock_call.side_effect = [None, subprocess.CalledProcessError(1, 'Test')]

    # Return immediately with fewer than two interfaces.
    network_setup.NetworkSetup.EnableNetworkInterfaces(self.mock_setup, None)
    network_setup.NetworkSetup.EnableNetworkInterfaces(self.mock_setup, [])
    # Enable interfaces.
    network_setup.NetworkSetup.EnableNetworkInterfaces(
        self.mock_setup, ['A', 'B'])
    self.assertEqual(self.mock_setup.interfaces, set(['A', 'B']))
    # Add a new interface.
    network_setup.NetworkSetup.EnableNetworkInterfaces(
        self.mock_setup, ['A', 'B', 'C'])
    self.assertEqual(self.mock_setup.interfaces, set(['A', 'B', 'C']))
    # Interfaces are already enabled.
    network_setup.NetworkSetup.EnableNetworkInterfaces(
        self.mock_setup, ['A', 'B', 'C'])
    self.assertEqual(self.mock_setup.interfaces, set(['A', 'B', 'C']))
    # A single interface is enabled by default.
    network_setup.NetworkSetup.EnableNetworkInterfaces(self.mock_setup, ['D'])
    self.assertEqual(self.mock_setup.interfaces, set(['D']))
    # Run a user supplied command successfully.
    self.mock_setup.dhcp_command = 'success'
    network_setup.NetworkSetup.EnableNetworkInterfaces(
        self.mock_setup, ['E', 'F'])
    self.assertEqual(self.mock_setup.interfaces, set(['E', 'F']))
    # Run a user supplied command and logger error messages.
    self.mock_setup.dhcp_command = 'failure'
    network_setup.NetworkSetup.EnableNetworkInterfaces(
        self.mock_setup, ['G', 'H'])
    self.assertEqual(self.mock_setup.interfaces, set(['G', 'H']))
    expected_calls = [
        mock.call.logger.info(mock.ANY, ['A', 'B']),
        mock.call.enable(['A', 'B'], mock.ANY, dhclient_script='/bin/script'),
        mock.call.logger.info(mock.ANY, ['A', 'B', 'C']),
        mock.call.enable(
            ['A', 'B', 'C'], mock.ANY, dhclient_script='/bin/script'),
        mock.call.logger.info(mock.ANY, ['D']),
        mock.call.logger.info(mock.ANY, ['E', 'F']),
        mock.call.call(['success']),
        mock.call.logger.info(mock.ANY, ['G', 'H']),
        mock.call.call(['failure']),
        mock.call.logger.warning(mock.ANY),
    ]
    self.assertEqual(mocks.mock_calls, expected_calls)
