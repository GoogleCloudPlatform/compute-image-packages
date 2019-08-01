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

"""Unittest for boto_config.py module."""

from google_compute_engine.boto import boto_config
from google_compute_engine.test_compat import mock
from google_compute_engine.test_compat import unittest


class BotoConfigTest(unittest.TestCase):

  def setUp(self):
    self.project_id = 'project'
    boto_config.BotoConfig.boto_config = 'config'
    boto_config.BotoConfig.boto_config_template = 'template'
    boto_config.BotoConfig.boto_config_script = '/tmp/test.py'
    boto_config.BotoConfig.boto_config_header = '%s %s'

  @mock.patch('google_compute_engine.boto.boto_config.metadata_watcher')
  @mock.patch('google_compute_engine.boto.boto_config.logger')
  @mock.patch('google_compute_engine.boto.boto_config.config_manager')
  def testCreateConfig(self, mock_config, mock_logger, mock_watcher):
    mock_config_instance = mock.Mock()
    mock_config.ConfigManager.return_value = mock_config_instance
    mocks = mock.Mock()
    mocks.attach_mock(mock_config.ConfigManager, 'config')
    mocks.attach_mock(mock_config_instance.SetOption, 'set')
    mocks.attach_mock(mock_config_instance.WriteConfig, 'write')
    mocks.attach_mock(mock_logger, 'logger')
    mocks.attach_mock(mock_watcher, 'watcher')
    mock_logger_instance = mock.Mock()
    mock_logger.Logger.return_value = mock_logger_instance

    boto_config.BotoConfig(self.project_id, debug=True)
    expected_calls = [
        mock.call.logger.Logger(name=mock.ANY, debug=True),
        mock.call.watcher.MetadataWatcher(logger=mock_logger_instance),
        mock.call.config(
            config_file='template', config_header='/tmp/test.py template'),
        mock.call.set('GSUtil', 'default_project_id', self.project_id),
        mock.call.set('GSUtil', 'default_api_version', '2'),
        mock.call.set('GoogleCompute', 'service_account', 'default'),
        mock.call.write(config_file='config'),
    ]
    self.assertEqual(mocks.mock_calls, expected_calls)

  @mock.patch('google_compute_engine.boto.boto_config.metadata_watcher')
  @mock.patch('google_compute_engine.boto.boto_config.config_manager')
  def testCreateConfigProjectId(self, mock_config, mock_watcher):
    mock_config_instance = mock.Mock()
    mock_config.ConfigManager.return_value = mock_config_instance
    mock_watcher_instance = mock.Mock()
    mock_watcher.MetadataWatcher.return_value = mock_watcher_instance
    mock_watcher_instance.GetMetadata.return_value = self.project_id

    boto_config.BotoConfig()
    mock_watcher_instance.GetMetadata.assert_called_once_with(
        metadata_key='project/project-id', recursive=False)
    expected_calls = [
        mock.call('GSUtil', 'default_project_id', self.project_id),
    ]
    mock_config_instance.SetOption.assert_has_calls(expected_calls)

  @mock.patch('google_compute_engine.boto.boto_config.metadata_watcher')
  @mock.patch('google_compute_engine.boto.boto_config.config_manager')
  def testCreateConfigExit(self, mock_config, mock_watcher):
    mock_config_instance = mock.Mock()
    mock_config.ConfigManager.return_value = mock_config_instance
    mock_watcher_instance = mock.Mock()
    mock_watcher.MetadataWatcher.return_value = mock_watcher_instance
    mock_watcher_instance.GetMetadata.return_value = None

    boto_config.BotoConfig()
    mock_watcher_instance.GetMetadata.assert_called_once_with(
        metadata_key='project/project-id', recursive=False)
    mock_config.SetOption.assert_not_called()


if __name__ == '__main__':
  unittest.main()
