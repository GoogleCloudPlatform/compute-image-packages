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

"""Unittest for instance_config.py module."""

from google_compute_engine.instance_setup import instance_config
from google_compute_engine.test_compat import mock
from google_compute_engine.test_compat import unittest


class InstanceConfigTest(unittest.TestCase):

  def setUp(self):
    instance_config.InstanceConfig.instance_config = 'config'
    instance_config.InstanceConfig.instance_config_template = 'template'
    instance_config.InstanceConfig.instance_config_script = '/tmp/test.py'
    instance_config.InstanceConfig.instance_config_header = '%s %s'
    instance_config.InstanceConfig.instance_config_options = {
        'third': {
            'e': '3',
            'c': '1',
            'd': '2',
        },
        'first': {
            'a': 'false',
        },
        'second': {
            'b': 'true',
        },
    }

  @mock.patch('google_compute_engine.instance_setup.instance_config.config_manager.ConfigManager.SetOption')
  @mock.patch('google_compute_engine.instance_setup.instance_config.config_manager.ConfigManager.__init__')
  def testInstanceConfig(self, mock_init, mock_set):
    mocks = mock.Mock()
    mocks.attach_mock(mock_init, 'init')
    mocks.attach_mock(mock_set, 'set')

    instance_config.InstanceConfig()
    expected_calls = [
        mock.call.init(
            config_file='template', config_header='/tmp/test.py template'),
        mock.call.set('first', 'a', 'false', overwrite=False),
        mock.call.set('second', 'b', 'true', overwrite=False),
        mock.call.set('third', 'c', '1', overwrite=False),
        mock.call.set('third', 'd', '2', overwrite=False),
        mock.call.set('third', 'e', '3', overwrite=False),
    ]
    self.assertEqual(mocks.mock_calls, expected_calls)

  @mock.patch('google_compute_engine.instance_setup.instance_config.config_manager.ConfigManager.WriteConfig')
  def testWriteConfig(self, mock_write):
    mock_config = instance_config.InstanceConfig()
    instance_config.InstanceConfig.WriteConfig(mock_config)
    mock_write.assert_called_once_with(config_file='config')


if __name__ == '__main__':
  unittest.main()
