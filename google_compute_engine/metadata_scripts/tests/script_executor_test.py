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

"""Unittest for script_executor.py module."""

import stat

from google_compute_engine.metadata_scripts import script_executor
from google_compute_engine.test_compat import mock
from google_compute_engine.test_compat import unittest


class ScriptExecutorTest(unittest.TestCase):

  def setUp(self):
    self.script_type = 'test'
    self.metadata_script = '/tmp/script'
    self.mock_logger = mock.Mock()
    self.executor = script_executor.ScriptExecutor(
        self.mock_logger, self.script_type)

  @mock.patch('google_compute_engine.metadata_scripts.script_executor.os')
  def testMakeExecutable(self, mock_os):
    st_mode = 1
    chmod_mode = st_mode + stat.S_IEXEC
    mock_os_stat = mock.Mock()
    mock_os_stat.st_mode = st_mode
    mock_os.stat.return_value = mock_os_stat
    self.executor._MakeExecutable(self.metadata_script)
    mock_os.chmod.assert_called_once_with(self.metadata_script, chmod_mode)

  @mock.patch('google_compute_engine.metadata_scripts.script_executor.subprocess')
  def testRunScript(self, mock_subprocess):
    mock_readline = mock.Mock()
    mock_readline.side_effect = [bytes(b'a\n'), bytes(b'b\n'), bytes(b'')]
    mock_stdout = mock.Mock()
    mock_stdout.readline = mock_readline
    mock_process = mock.Mock()
    mock_process.poll.return_value = 0
    mock_process.stdout = mock_stdout
    mock_process.returncode = 1
    mock_subprocess.Popen.return_value = mock_process
    metadata_key = '%s-script' % self.script_type

    self.executor._RunScript(metadata_key, self.metadata_script)
    expected_calls = [
        mock.call('%s: %s', metadata_key, 'a'),
        mock.call('%s: %s', metadata_key, 'b'),
        mock.call('%s: Return code %s.', metadata_key, 1),
    ]
    self.assertEqual(self.mock_logger.info.mock_calls, expected_calls)
    mock_subprocess.Popen.assert_called_once_with(
        self.metadata_script, shell=True, executable='/bin/bash',
        stderr=mock_subprocess.STDOUT, stdout=mock_subprocess.PIPE)
    mock_process.poll.assert_called_once_with()

  def testRunScripts(self):
    self.executor._MakeExecutable = mock.Mock()
    self.executor._RunScript = mock.Mock()
    mocks = mock.Mock()
    mocks.attach_mock(self.executor._MakeExecutable, 'make_executable')
    mocks.attach_mock(self.executor._RunScript, 'run_script')
    mocks.attach_mock(self.mock_logger, 'logger')
    script_dict = {
        '%s-script' % self.script_type: 'a',
        '%s-script-key' % self.script_type: 'b',
        '%s-script-url' % self.script_type: 'c',
    }

    self.executor.RunScripts(script_dict)
    expected_calls = [
        mock.call.make_executable('c'),
        mock.call.run_script('%s-script-url' % self.script_type, 'c'),
        mock.call.make_executable('a'),
        mock.call.run_script('%s-script' % self.script_type, 'a'),
    ]
    self.assertEqual(mocks.mock_calls, expected_calls)

  def testRunScriptsEmpty(self):
    self.executor._MakeExecutable = mock.Mock()
    self.executor._RunScript = mock.Mock()
    mocks = mock.Mock()
    mocks.attach_mock(self.executor._MakeExecutable, 'make_executable')
    mocks.attach_mock(self.executor._RunScript, 'run_script')
    mocks.attach_mock(self.mock_logger, 'logger')
    script_dict = {
        '%s-invalid' % self.script_type: 'script',
    }

    self.executor.RunScripts(script_dict)
    expected_calls = [
        mock.call.logger.info(mock.ANY, self.script_type),
    ]
    self.assertEqual(mocks.mock_calls, expected_calls)


if __name__ == '__main__':
  unittest.main()
