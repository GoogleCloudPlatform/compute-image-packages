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

"""Unittest for compute_auth.py module."""

import sys

from google_compute_engine.test_compat import mock
from google_compute_engine.test_compat import unittest

if sys.version_info < (3, 0):
  from google_compute_engine.boto import compute_auth


@unittest.skipIf(sys.version_info > (3, 0), 'Skipping for python3.')
class ComputeAuthTest(unittest.TestCase):

  def setUp(self):
    self.metadata_key = 'instance/service-accounts'
    self.service_account = 'service_account'
    self.mock_config = mock.Mock()
    self.mock_config.get.return_value = self.service_account
    self.mock_provider = mock.Mock()
    self.mock_provider.name = 'google'

  @mock.patch('google_compute_engine.boto.compute_auth.metadata_watcher')
  @mock.patch('google_compute_engine.boto.compute_auth.logger')
  def testCreateConfig(self, mock_logger, mock_watcher):
    scopes = list(compute_auth.GS_SCOPES)[1:2]
    service_accounts = {self.service_account: {'scopes': scopes}}
    mock_watcher.GetMetadata.return_value = service_accounts
    mock_watcher.MetadataWatcher.return_value = mock_watcher
    mocks = mock.Mock()
    mocks.attach_mock(mock_watcher, 'watcher')
    mocks.attach_mock(mock_logger, 'logger')
    mocks.attach_mock(self.mock_config, 'config')
    mock_logger_instance = mock.Mock()
    mock_logger.Logger.return_value = mock_logger_instance

    mock_compute_auth = compute_auth.ComputeAuth(
        None, self.mock_config, self.mock_provider)
    expected_calls = [
        mock.call.logger.Logger(name=mock.ANY),
        mock.call.watcher.MetadataWatcher(logger=mock_logger_instance),
        mock.call.config.get('GoogleCompute', 'service_account', ''),
        mock.call.watcher.GetMetadata(metadata_key=self.metadata_key)
    ]
    self.assertEqual(mocks.mock_calls, expected_calls)
    self.assertEqual(mock_compute_auth.scopes, scopes)

  @mock.patch('google_compute_engine.boto.compute_auth.metadata_watcher')
  def testCreateConfigNoScopes(self, mock_watcher):
    mock_watcher.GetMetadata.return_value = {}
    mock_watcher.MetadataWatcher.return_value = mock_watcher

    with self.assertRaises(compute_auth.auth_handler.NotReadyToAuthenticate):
      compute_auth.ComputeAuth(None, self.mock_config, self.mock_provider)

  def testCreateConfigNoServiceAccount(self):
    self.mock_config.get.return_value = None

    with self.assertRaises(compute_auth.auth_handler.NotReadyToAuthenticate):
      compute_auth.ComputeAuth(None, self.mock_config, self.mock_provider)

  @mock.patch('google_compute_engine.boto.compute_auth.metadata_watcher')
  def testGetAccessToken(self, mock_watcher):
    mock_auth = mock.create_autospec(compute_auth.ComputeAuth)
    mock_auth.watcher = mock_watcher
    mock_auth.metadata_key = self.metadata_key
    mock_auth.service_account = self.service_account
    mock_watcher.GetMetadata.side_effect = [
        {self.service_account: {'token': {'access_token': 'test'}}},
        {},
    ]

    self.assertEqual(
        compute_auth.ComputeAuth._GetAccessToken(mock_auth), 'test')
    self.assertEqual(
        compute_auth.ComputeAuth._GetAccessToken(mock_auth), None)
    expected_calls = [mock.call(metadata_key=self.metadata_key)] * 2
    self.assertEqual(mock_watcher.GetMetadata.mock_calls, expected_calls)

  @mock.patch('google_compute_engine.boto.compute_auth.metadata_watcher')
  def testAddAuth(self, mock_watcher):
    mock_auth = mock.create_autospec(compute_auth.ComputeAuth)
    mock_auth._GetAccessToken.return_value = 'token'
    mock_request = mock.Mock()
    mock_request.headers = {}

    compute_auth.ComputeAuth.add_auth(mock_auth, mock_request)
    self.assertEqual(mock_request.headers['Authorization'], 'OAuth token')


if __name__ == '__main__':
  unittest.main()
