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

"""Unittest for ip_forwarding_utils.py module."""

from google_compute_engine.ip_forwarding import ip_forwarding_utils
from google_compute_engine.test_compat import mock
from google_compute_engine.test_compat import unittest


class IpForwardingUtilsTest(unittest.TestCase):

  def setUp(self):
    self.mock_logger = mock.Mock()
    self.options = {'hello': 'world'}
    self.mock_utils = ip_forwarding_utils.IpForwardingUtils(self.mock_logger)
    self.mock_utils.options = self.options

  @mock.patch('google_compute_engine.ip_forwarding.ip_forwarding_utils.subprocess')
  def testRunIpRoute(self, mock_subprocess):
    mock_process = mock.Mock()
    mock_process.returncode = 0
    mock_process.communicate.return_value = ('out', '')
    mock_subprocess.Popen.return_value = mock_process
    args = ['foo', 'bar']
    options = {'one': 'two'}

    self.assertEqual(
        self.mock_utils._RunIpRoute(args=args, options=options), 'out')
    command = ['ip', 'route', 'foo', 'bar', 'one', 'two']
    mock_subprocess.Popen.assert_called_once_with(
        command, stdout=mock_subprocess.PIPE, stderr=mock_subprocess.PIPE)
    mock_process.communicate.assert_called_once_with()
    self.mock_logger.warning.assert_not_called()

  @mock.patch('google_compute_engine.ip_forwarding.ip_forwarding_utils.subprocess')
  def testRunIpRouteReturnCode(self, mock_subprocess):
    mock_process = mock.Mock()
    mock_process.returncode = 1
    mock_process.communicate.return_value = ('out', 'error\n')
    mock_subprocess.Popen.return_value = mock_process

    self.assertEqual(
        self.mock_utils._RunIpRoute(args=['foo', 'bar'], options=self.options),
        '')
    command = ['ip', 'route', 'foo', 'bar', 'hello', 'world']
    self.mock_logger.warning.assert_called_once_with(mock.ANY, command, 'error')

  @mock.patch('google_compute_engine.ip_forwarding.ip_forwarding_utils.subprocess')
  def testRunIpRouteException(self, mock_subprocess):
    mock_subprocess.Popen.side_effect = OSError('Test Error')

    self.assertEqual(
        self.mock_utils._RunIpRoute(args=['foo', 'bar'], options=self.options),
        '')
    command = ['ip', 'route', 'foo', 'bar', 'hello', 'world']
    self.mock_logger.warning.assert_called_once_with(
        mock.ANY, command, 'Test Error')

  def testGetDefaultInterface(self):
    mock_run = mock.Mock()
    mock_run.side_effect = [
        bytes(b''),
        bytes(b'invalid route\n'),
        bytes(b'default invalid interface\n'),
        bytes(b'default dev\n'),
        bytes(b'\n\n\ndefault dev interface\n\n\n'),
        bytes(b'default via ip dev interface\nip default eth0\n'),
        bytes(b'ip default eth0\ndefault via ip dev interface\n'),
    ]
    self.mock_utils._RunIpRoute = mock_run

    # Invalid routes default to 'eth0'.
    self.assertEqual(self.mock_utils._GetDefaultInterface(), 'eth0')
    self.assertEqual(self.mock_utils._GetDefaultInterface(), 'eth0')
    self.assertEqual(self.mock_utils._GetDefaultInterface(), 'eth0')
    self.assertEqual(self.mock_utils._GetDefaultInterface(), 'eth0')

    # Valid routes where the expected response is 'interface'.
    self.assertEqual(self.mock_utils._GetDefaultInterface(), 'interface')
    self.assertEqual(self.mock_utils._GetDefaultInterface(), 'interface')
    self.assertEqual(self.mock_utils._GetDefaultInterface(), 'interface')

  def testParseForwardedIps(self):
    self.assertEqual(self.mock_utils.ParseForwardedIps(None), [])
    self.assertEqual(self.mock_utils.ParseForwardedIps([]), [])
    self.assertEqual(self.mock_utils.ParseForwardedIps([None]), [])
    self.assertEqual(self.mock_utils.ParseForwardedIps(['invalid']), [])
    self.assertEqual(self.mock_utils.ParseForwardedIps(['1a1a1a1']), [])
    self.assertEqual(self.mock_utils.ParseForwardedIps(['1.1.1.1.1']), [])
    self.assertEqual(self.mock_utils.ParseForwardedIps(['1111.1.1.1']), [])
    self.assertEqual(self.mock_utils.ParseForwardedIps(['1.1.1.1111']), [])
    expected_calls = [
        mock.call.warning(mock.ANY, None),
        mock.call.warning(mock.ANY, 'invalid'),
        mock.call.warning(mock.ANY, '1a1a1a1'),
        mock.call.warning(mock.ANY, '1.1.1.1.1'),
        mock.call.warning(mock.ANY, '1111.1.1.1'),
        mock.call.warning(mock.ANY, '1.1.1.1111'),
    ]
    self.assertEqual(self.mock_logger.mock_calls, expected_calls)

  def testParseForwardedIpsComplex(self):
    forwarded_ips = {
        '{{}}\n\"hello\"\n!@#$%^&*()\n\n': False,
        '1111.1.1.1': False,
        '1.1.1.1': True,
        'hello': False,
        '123.123.123.123': True,
        '1.1.1.': False,
        '1.1.1.a': False,
        None: False,
        '1.0.0.0': True,
    }
    input_ips = forwarded_ips.keys()
    valid_ips = [ip for ip, valid in forwarded_ips.items() if valid]
    invalid_ips = [ip for ip, valid in forwarded_ips.items() if not valid]

    self.assertEqual(self.mock_utils.ParseForwardedIps(input_ips), valid_ips)
    expected_calls = [mock.call.warning(mock.ANY, ip) for ip in invalid_ips]
    self.assertEqual(self.mock_logger.mock_calls, expected_calls)

  def testGetForwardedIps(self):
    mock_run = mock.Mock()
    mock_run.return_value = ''
    mock_parse = mock.Mock()
    mock_parse.return_value = ['Test']
    self.mock_utils._RunIpRoute = mock_run
    self.mock_utils.ParseForwardedIps = mock_parse

    self.assertEqual(self.mock_utils.GetForwardedIps(), ['Test'])
    mock_run.assert_called_once_with(
        args=['ls', 'table', 'local', 'type', 'local'], options=self.options)
    mock_parse.assert_called_once_with([])

  def testGetForwardedIpsSplit(self):
    mock_run = mock.Mock()
    mock_run.return_value = 'a\nb\n'
    mock_parse = mock.Mock()
    self.mock_utils._RunIpRoute = mock_run
    self.mock_utils.ParseForwardedIps = mock_parse

    self.mock_utils.GetForwardedIps()
    mock_parse.assert_called_once_with(['a', 'b'])

  def testAddForwardedIp(self):
    mock_run = mock.Mock()
    self.mock_utils._RunIpRoute = mock_run

    self.mock_utils.AddForwardedIp('1.1.1.1')
    mock_run.assert_called_once_with(
        args=['add', 'to', 'local', '1.1.1.1/32'], options=self.options)

  def testRemoveForwardedIp(self):
    mock_run = mock.Mock()
    self.mock_utils._RunIpRoute = mock_run

    self.mock_utils.RemoveForwardedIp('1.1.1.1')
    mock_run.assert_called_once_with(
        args=['delete', 'to', 'local', '1.1.1.1/32'], options=self.options)


if __name__ == '__main__':
  unittest.main()
