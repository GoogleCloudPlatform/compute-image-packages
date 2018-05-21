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

"""Unittest for script_manager.py module."""

from google_compute_engine.metadata_scripts import script_manager
from google_compute_engine.test_compat import mock
from google_compute_engine.test_compat import unittest


class ScriptManagerTest(unittest.TestCase):

  @mock.patch('google_compute_engine.metadata_scripts.script_manager.script_retriever')
  @mock.patch('google_compute_engine.metadata_scripts.script_manager.logger')
  @mock.patch('google_compute_engine.metadata_scripts.script_manager.script_executor')
  @mock.patch('google_compute_engine.metadata_scripts.script_manager.shutil.rmtree')
  @mock.patch('google_compute_engine.metadata_scripts.script_manager.tempfile.mkdtemp')
  def testRunScripts(
      self, mock_mkdir, mock_rmtree, mock_executor, mock_logger,
      mock_retriever):
    mock_logger_instance = mock.Mock()
    mock_logger.Logger.return_value = mock_logger_instance
    mock_retriever_instance = mock.Mock()
    mock_retriever.ScriptRetriever.return_value = mock_retriever_instance
    mocks = mock.Mock()
    mocks.attach_mock(mock_mkdir, 'mkdir')
    mocks.attach_mock(mock_rmtree, 'rmtree')
    mocks.attach_mock(mock_executor, 'executor')
    mocks.attach_mock(mock_logger, 'logger')
    mocks.attach_mock(mock_retriever, 'retriever')
    run_dir = '/var/run'
    script_type = 'test'
    script_name = '%s-script' % script_type
    script_prefix = '%s-' % script_type
    test_dir = 'test-dir'
    test_dict = {'test': 'dict'}
    mock_mkdir.return_value = test_dir
    mock_retriever_instance.GetScripts.return_value = test_dict

    script_manager.ScriptManager(script_type, run_dir=run_dir)
    expected_calls = [
        mock.call.logger.Logger(
            name=script_name, debug=False, facility=mock.ANY),
        mock.call.retriever.ScriptRetriever(mock_logger_instance, script_type),
        mock.call.executor.ScriptExecutor(
            mock_logger_instance, script_type, default_shell=None),
        mock.call.mkdir(prefix=script_prefix, dir=run_dir),
        mock.call.logger.Logger().info(mock.ANY, script_type),
        mock.call.retriever.ScriptRetriever().GetScripts(test_dir),
        mock.call.executor.ScriptExecutor().RunScripts(test_dict),
        mock.call.logger.Logger().info(mock.ANY, script_type),
        mock.call.rmtree(test_dir),
    ]
    self.assertEqual(mocks.mock_calls, expected_calls)


if __name__ == '__main__':
  unittest.main()
