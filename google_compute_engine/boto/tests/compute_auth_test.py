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

from google_compute_engine.boto import compute_auth
from google_compute_engine.test_compat import mock
from google_compute_engine.test_compat import unittest


class ComputeAuthTest(unittest.TestCase):

  def setUp(self):
    self.service_account = 'service_account'
    self.mock_config = mock.Mock()
    self.mock_config.get.return_value = self.service_account
    self.mock_provider = mock.Mock()
    self.mock_provider.name = 'google'

  @mock.patch('google_compute_engine.boto.compute_auth.metadata_watcher')
  @mock.patch('google_compute_engine.boto.compute_auth.logger')
  def testCreateConfig(self, mock_logger, mock_watcher):
    scopes = list(compute_auth.GS_SCOPES)[1:2]
    mock_watcher.GetMetadata.return_value = scopes
    mock_watcher.MetadataWatcher.return_value = mock_watcher
    scopes_key = 'instance/service-accounts/%s/scopes' % self.service_account
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
        mock.call.watcher.GetMetadata(metadata_key=scopes_key, recursive=False),
    ]
    self.assertEqual(mocks.mock_calls, expected_calls)
    self.assertEqual(mock_compute_auth.scopes, scopes)

  def testCreateConfigException(self):
    self.mock_config.get.return_value = None

    with self.assertRaises(compute_auth.auth_handler.NotReadyToAuthenticate):
      compute_auth.ComputeAuth(None, self.mock_config, self.mock_provider)

  @mock.patch('google_compute_engine.boto.compute_auth.metadata_watcher')
  def testGetAccessToken(self, mock_watcher):
    mock_watcher.MetadataWatcher.return_value = mock_watcher
    mock_watcher.GetMetadata.side_effect = [
        list(compute_auth.GS_SCOPES),  # The Google Storage scopes.
        {'access_token': 'token'},  # The access token.
        {},  # The access token second query.
    ]
    mock_compute_auth = compute_auth.ComputeAuth(
        None, self.mock_config, self.mock_provider)
    self.assertEqual(mock_compute_auth._GetAccessToken(), 'token')
    self.assertEqual(mock_compute_auth._GetAccessToken(), None)

    token_key = 'instance/service-accounts/%s/token' % self.service_account
    expected_calls = [
        mock.ANY,
        mock.call(metadata_key=token_key, recursive=False),
        mock.call(metadata_key=token_key, recursive=False),
    ]
    self.assertEqual(mock_watcher.GetMetadata.mock_calls, expected_calls)

  @mock.patch('google_compute_engine.boto.compute_auth.metadata_watcher')
  def testAddAuth(self, mock_watcher):
    mock_request = mock.Mock()
    mock_request.headers = {}
    mock_watcher.MetadataWatcher.return_value = mock_watcher
    mock_watcher.GetMetadata.side_effect = [
        list(compute_auth.GS_SCOPES),  # The Google Storage scopes.
        {'access_token': 'token'},  # The access token.
    ]
    mock_compute_auth = compute_auth.ComputeAuth(
        None, self.mock_config, self.mock_provider)
    mock_compute_auth.add_auth(mock_request)
    self.assertEqual(mock_request.headers['Authorization'], 'OAuth token')


if __name__ == '__main__':
  unittest.main()
