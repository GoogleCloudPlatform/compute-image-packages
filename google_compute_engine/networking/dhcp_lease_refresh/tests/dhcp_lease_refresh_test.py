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

"""Unittest for dhcp_lease_refresh.py module."""

from google_compute_engine.networking.dhcp_lease_refresh import dhcp_lease_refresh
from google_compute_engine.test_compat import mock
from google_compute_engine.test_compat import unittest


class DhcpRefreshTest(unittest.TestCase):

  def setUp(self):
    self.mock_logger = mock.Mock()
    self.mock_distro_utils = mock.Mock()
    self.mock_setup = mock.create_autospec(dhcp_lease_refresh.DhcpLeaseRefresh)
    self.mock_setup.logger = self.mock_logger
    self.mock_setup.distro_utils = self.mock_distro_utils

  @mock.patch('google_compute_engine.networking.dhcp_lease_refresh.dhcp_lease_refresh.logger')
  @mock.patch('google_compute_engine.networking.dhcp_lease_refresh.dhcp_lease_refresh.distro_utils')
  def testDhcpLeaseRefresh(self, mock_distro_utils, mock_logger):
    mock_logger_instance = mock.Mock()
    mock_logger.Logger.return_value = mock_logger_instance
    mocks = mock.Mock()
    mocks.attach_mock(mock_logger, 'logger')
    mocks.attach_mock(mock_distro_utils, 'distro')
    dhcpv6_tokens = {'A': None, 'B': None}

    dhcp_lease_refresh.DhcpLeaseRefresh(dhcpv6_tokens, debug=True)
    expected_calls = [
        mock.call.logger.Logger(name=mock.ANY, debug=True, facility=mock.ANY),
        mock.call.distro.Utils(debug=True),
    ]
    self.assertEqual(mocks.mock_calls, expected_calls)

  def testHandleDhcpLeaseRefreshWithTokenChange(self):
    mocks = mock.Mock()
    mocks.attach_mock(self.mock_distro_utils, 'distro_utils')
    self.mock_setup.dhcpv6_tokens = {'eth1': 'a', 'eth2': 'b'}
    expected_calls = [
        mock.call.distro_utils.RefreshDhcpV6Lease('eth1'),
    ]

    dhcp_lease_refresh.DhcpLeaseRefresh.HandleDhcpLeaseRefresh(
        self.mock_setup, 'eth1', dhcpv6_refresh_token='x')
    self.assertEqual(self.mock_setup.dhcpv6_tokens.get('eth1'), 'x')
    self.assertEqual(mocks.mock_calls, expected_calls)

  def testHandleDhcpLeaseRefreshWithoutTokenChange(self):
    mocks = mock.Mock()
    mocks.attach_mock(self.mock_distro_utils, 'distro_utils')
    self.mock_setup.dhcpv6_tokens = {'eth1': 'a', 'eth2': 'b'}
    expected_calls = []

    dhcp_lease_refresh.DhcpLeaseRefresh.HandleDhcpLeaseRefresh(
        self.mock_setup, 'eth1', dhcpv6_refresh_token='a')
    self.assertEqual(self.mock_setup.dhcpv6_tokens.get('eth1'), 'a')
    self.assertEqual(mocks.mock_calls, expected_calls)
