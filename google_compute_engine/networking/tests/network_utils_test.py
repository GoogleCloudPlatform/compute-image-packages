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

"""Unittest for network_utils.py module."""

from google_compute_engine.networking import network_utils
from google_compute_engine.test_compat import builtin
from google_compute_engine.test_compat import mock
from google_compute_engine.test_compat import unittest


class NetworkUtilsTest(unittest.TestCase):

  def setUp(self):
    self.mock_logger = mock.Mock()
    self.interfaces = {'address': 'interface'}
    self.mock_utils = network_utils.NetworkUtils(self.mock_logger)
    self.mock_utils.interfaces = self.interfaces

  @mock.patch('google_compute_engine.networking.network_utils.netifaces', False)
  @mock.patch('google_compute_engine.networking.network_utils.os.listdir')
  def testCreateInterfaceMapSysfs(self, mock_listdir):
    mock_open = mock.mock_open()
    interface_map = {
        '1': 'a',
        '2': 'b',
        '3': 'c',
    }
    mock_listdir.return_value = interface_map.values()

    with mock.patch('%s.open' % builtin, mock_open, create=False):
      addresses = interface_map.keys()
      addresses = ['%s\n' % address for address in addresses]
      mock_open().read.side_effect = interface_map.keys()
      self.assertEqual(self.mock_utils._CreateInterfaceMap(), interface_map)

  @mock.patch('google_compute_engine.networking.network_utils.netifaces', False)
  @mock.patch('google_compute_engine.networking.network_utils.os.listdir')
  def testCreateInterfaceMapSysfsError(self, mock_listdir):
    mock_open = mock.mock_open()
    mock_listdir.return_value = ['a', 'b', 'c']

    with mock.patch('%s.open' % builtin, mock_open, create=False):
      mock_open().read.side_effect = [
          '1', OSError('OSError'), IOError('IOError')]
      self.assertEqual(self.mock_utils._CreateInterfaceMap(), {'1': 'a'})
      expected_calls = [
          mock.call.warning(mock.ANY, 'b', 'OSError'),
          mock.call.warning(mock.ANY, 'c', 'IOError'),
      ]
      self.assertEqual(self.mock_logger.mock_calls, expected_calls)

  @mock.patch('google_compute_engine.networking.network_utils.netifaces.AF_LINK', 88)
  @mock.patch('google_compute_engine.networking.network_utils.netifaces')
  def testCreateInterfaceMapNetifaces(self, mock_netifaces):
    interface_map = {
        '11:11:11:11:11:11': 'a',
        '22:22:22:22:22:22': 'b',
        '33:33:33:33:33:33': 'c',
    }
    ifaddress_map = {
        'a': {mock_netifaces.AF_LINK: [{'addr': '11:11:11:11:11:11'}]},
        'b': {mock_netifaces.AF_LINK: [{'addr': '22:22:22:22:22:22'}]},
        'c': {mock_netifaces.AF_LINK: [{'addr': '33:33:33:33:33:33'}]},
    }
    mock_netifaces.interfaces.return_value = interface_map.values()
    mock_netifaces.ifaddresses.side_effect = (
        lambda interface: ifaddress_map[interface])
    self.assertEqual(self.mock_utils._CreateInterfaceMap(), interface_map)

  @mock.patch('google_compute_engine.networking.network_utils.netifaces.AF_LINK', 88)
  @mock.patch('google_compute_engine.networking.network_utils.netifaces')
  def testCreateInterfaceMapNetifacesError(self, mock_netifaces):
    ifaddress_map = {
        'a': {mock_netifaces.AF_LINK: [{'addr': '11:11:11:11:11:11'}]},
        'b': {},
        'c': {mock_netifaces.AF_LINK: [{'addr': ''}]},
    }
    mock_netifaces.interfaces.return_value = ['a', 'b', 'c']
    mock_netifaces.ifaddresses.side_effect = (
        lambda interface: ifaddress_map[interface])

    self.assertEqual(
        self.mock_utils._CreateInterfaceMap(), {'11:11:11:11:11:11': 'a'})
    expected_calls = [
        mock.call.warning(mock.ANY, 'b'),
        mock.call.warning(mock.ANY, 'c'),
    ]
    self.assertEqual(self.mock_logger.mock_calls, expected_calls)

  def testGetNetworkInterface(self):
    self.assertIsNone(self.mock_utils.GetNetworkInterface('invalid'))
    self.assertEqual(
        self.mock_utils.GetNetworkInterface('address'), 'interface')
