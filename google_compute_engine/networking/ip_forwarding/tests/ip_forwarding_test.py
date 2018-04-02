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

"""Unittest for ip_forwarding.py module."""

from google_compute_engine.networking.ip_forwarding import ip_forwarding
from google_compute_engine.test_compat import mock
from google_compute_engine.test_compat import unittest


class IpForwardingTest(unittest.TestCase):

  def setUp(self):
    self.mock_logger = mock.Mock()
    self.mock_watcher = mock.Mock()
    self.mock_ip_forwarding_utils = mock.Mock()
    self.mock_setup = mock.create_autospec(ip_forwarding.IpForwarding)
    self.mock_setup.logger = self.mock_logger
    self.mock_setup.ip_forwarding_utils = self.mock_ip_forwarding_utils

  @mock.patch('google_compute_engine.networking.ip_forwarding.ip_forwarding.ip_forwarding_utils')
  @mock.patch('google_compute_engine.networking.ip_forwarding.ip_forwarding.logger')
  def testIpForwarding(self, mock_logger, mock_ip_forwarding_utils):
    mock_logger_instance = mock.Mock()
    mock_logger.Logger.return_value = mock_logger_instance
    mocks = mock.Mock()
    mocks.attach_mock(mock_logger, 'logger')
    mocks.attach_mock(mock_ip_forwarding_utils, 'forwarding')
    with mock.patch.object(ip_forwarding.IpForwarding, 'HandleForwardedIps'):

      ip_forwarding.IpForwarding(proto_id='66', debug=True)
      expected_calls = [
          mock.call.logger.Logger(name=mock.ANY, debug=True, facility=mock.ANY),
          mock.call.forwarding.IpForwardingUtils(
              logger=mock_logger_instance, proto_id='66'),
      ]
      self.assertEqual(mocks.mock_calls, expected_calls)

  def testLogForwardedIpChanges(self):
    ip_forwarding.IpForwarding._LogForwardedIpChanges(
        self.mock_setup, [], [], [], [], '1')
    ip_forwarding.IpForwarding._LogForwardedIpChanges(
        self.mock_setup, ['a'], ['a'], [], [], '2')
    ip_forwarding.IpForwarding._LogForwardedIpChanges(
        self.mock_setup, ['a'], [], [], ['a'], '3')
    ip_forwarding.IpForwarding._LogForwardedIpChanges(
        self.mock_setup, ['a', 'b'], ['b'], [], ['a'], '4')
    ip_forwarding.IpForwarding._LogForwardedIpChanges(
        self.mock_setup, ['a'], ['b'], ['b'], ['a'], '5')
    expected_calls = [
        mock.call.info(mock.ANY, '3', ['a'], None, None, ['a']),
        mock.call.info(mock.ANY, '4', ['a', 'b'], ['b'], None, ['a']),
        mock.call.info(mock.ANY, '5', ['a'], ['b'], ['b'], ['a']),
    ]
    self.assertEqual(self.mock_logger.mock_calls, expected_calls)

  def testAddForwardedIp(self):
    ip_forwarding.IpForwarding._AddForwardedIps(
        self.mock_setup, [], 'interface')
    self.assertEqual(self.mock_ip_forwarding_utils.mock_calls, [])

    ip_forwarding.IpForwarding._AddForwardedIps(
        self.mock_setup, ['a', 'b', 'c'], 'interface')
    expected_calls = [
        mock.call.AddForwardedIp('a', 'interface'),
        mock.call.AddForwardedIp('b', 'interface'),
        mock.call.AddForwardedIp('c', 'interface'),
    ]
    self.assertEqual(self.mock_ip_forwarding_utils.mock_calls, expected_calls)

  def testRemoveForwardedIp(self):
    ip_forwarding.IpForwarding._RemoveForwardedIps(
        self.mock_setup, [], 'interface')
    self.assertEqual(self.mock_ip_forwarding_utils.mock_calls, [])

    ip_forwarding.IpForwarding._RemoveForwardedIps(
        self.mock_setup, ['a', 'b', 'c'], 'interface')
    expected_calls = [
        mock.call.RemoveForwardedIp('a', 'interface'),
        mock.call.RemoveForwardedIp('b', 'interface'),
        mock.call.RemoveForwardedIp('c', 'interface'),
    ]
    self.assertEqual(self.mock_ip_forwarding_utils.mock_calls, expected_calls)

  def testHandleForwardedIps(self):
    configured = ['c', 'c', 'b', 'b', 'a', 'a']
    desired = ['d', 'd', 'c']
    mocks = mock.Mock()
    mocks.attach_mock(self.mock_ip_forwarding_utils, 'forwarding')
    mocks.attach_mock(self.mock_setup, 'setup')
    self.mock_ip_forwarding_utils.ParseForwardedIps.return_value = desired
    self.mock_ip_forwarding_utils.GetForwardedIps.return_value = configured
    forwarded_ips = 'forwarded ips'
    interface = 'interface'
    expected_add = ['d']
    expected_remove = ['a', 'b']

    ip_forwarding.IpForwarding.HandleForwardedIps(
        self.mock_setup, interface, forwarded_ips)
    expected_calls = [
        mock.call.forwarding.ParseForwardedIps(forwarded_ips),
        mock.call.forwarding.GetForwardedIps(interface),
        mock.call.setup._LogForwardedIpChanges(
            configured, desired, expected_add, expected_remove, interface),
        mock.call.setup._AddForwardedIps(expected_add, interface),
        mock.call.setup._RemoveForwardedIps(expected_remove, interface),
    ]
    self.assertEqual(mocks.mock_calls, expected_calls)
