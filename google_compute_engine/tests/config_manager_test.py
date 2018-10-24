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

"""Unittest for config_manager.py module."""

from google_compute_engine import config_manager
from google_compute_engine.test_compat import builtin
from google_compute_engine.test_compat import mock
from google_compute_engine.test_compat import unittest


def _HasOption(_, option):
  """Validate the option exists in the config file.

  Args:
    option: string, the config option to check.

  Returns:
    bool, True if test is not in the option name.
  """
  return 'test' not in option


def _HasSection(section):
  """Validate the section exists in the config file.

  Args:
    section: string, the config section to check.

  Returns:
    bool, True if test is not in the section name.
  """
  return 'test' not in section


class ConfigManagerTest(unittest.TestCase):

  option = 'option'
  section = 'section'
  value = 'value'

  def setUp(self):
    self.mock_config = mock.Mock()
    self.mock_config.has_option.side_effect = _HasOption
    self.mock_config.has_section.side_effect = _HasSection
    config_manager.parser.Parser = mock.Mock()
    config_manager.parser.Parser.return_value = self.mock_config

    self.config_file = 'test.cfg'
    self.config_header = 'Config file header.'

    self.mock_config_manager = config_manager.ConfigManager(
        config_file=self.config_file, config_header=self.config_header)

  def testAddHeader(self):
    mock_fp = mock.Mock()
    self.mock_config_manager._AddHeader(mock_fp)
    expected_calls = [
        mock.call('# %s' % self.config_header),
        mock.call('\n\n'),
    ]
    self.assertEqual(mock_fp.write.mock_calls, expected_calls)

  def testGetOptionString(self):
    self.mock_config_manager.GetOptionString(self.section, self.option)
    expected_calls = [
        mock.call.read(self.config_file),
        mock.call.has_option(self.section, self.option),
        mock.call.get(self.section, self.option),
    ]
    self.assertEqual(self.mock_config.mock_calls, expected_calls)

  def testGetOptionStringNoOption(self):
    option = 'test-option'
    self.assertIsNone(
        self.mock_config_manager.GetOptionString(self.section, option))
    expected_calls = [
        mock.call.read(self.config_file),
        mock.call.has_option(self.section, option),
    ]
    self.assertEqual(self.mock_config.mock_calls, expected_calls)

  def testGetOptionBool(self):
    self.mock_config_manager.GetOptionBool(self.section, self.option)
    expected_calls = [
        mock.call.read(self.config_file),
        mock.call.has_option(self.section, self.option),
        mock.call.getboolean(self.section, self.option),
    ]
    self.assertEqual(self.mock_config.mock_calls, expected_calls)

  def testGetOptionBoolNoOption(self):
    option = 'test-option'
    self.assertTrue(
        self.mock_config_manager.GetOptionBool(self.section, option))
    expected_calls = [
        mock.call.read(self.config_file),
        mock.call.has_option(self.section, option),
    ]
    self.assertEqual(self.mock_config.mock_calls, expected_calls)

  def testSetOption(self):
    self.mock_config_manager.SetOption(self.section, self.option, self.value)
    expected_calls = [
        mock.call.read(self.config_file),
        mock.call.has_section(self.section),
        mock.call.set(self.section, self.option, self.value),
    ]
    self.assertEqual(self.mock_config.mock_calls, expected_calls)

  def testSetOptionNoOverwrite(self):
    self.mock_config_manager.SetOption(
        self.section, self.option, self.value, overwrite=False)
    expected_calls = [
        mock.call.read(self.config_file),
        mock.call.has_option(self.section, self.option),
    ]
    self.assertEqual(self.mock_config.mock_calls, expected_calls)

  def testSetOptionNewSection(self):
    section = 'test-section'
    self.mock_config_manager.SetOption(section, self.option, self.value)
    expected_calls = [
        mock.call.read(self.config_file),
        mock.call.has_section(section),
        mock.call.add_section(section),
        mock.call.set(section, self.option, self.value),
    ]
    self.assertEqual(self.mock_config.mock_calls, expected_calls)

  def testWriteConfig(self):
    mock_open = mock.mock_open()
    with mock.patch('%s.open' % builtin, mock_open, create=False):
      self.mock_config_manager.WriteConfig()
      expected_calls = [
          mock.call('# %s' % self.config_header),
          mock.call('\n\n'),
      ]
      self.assertEqual(mock_open().write.mock_calls, expected_calls)

  @mock.patch('google_compute_engine.config_manager.file_utils')
  def testWriteConfigNoHeader(self, mock_lock):
    self.mock_config_manager = config_manager.ConfigManager(
        config_file='/tmp/file.cfg')
    mock_open = mock.mock_open()
    with mock.patch('%s.open' % builtin, mock_open, create=False):
      self.mock_config_manager.WriteConfig()
      mock_open().write.assert_not_called()
    mock_lock.LockFile.assert_called_once_with('/var/lock/google_file.lock')

  @mock.patch('google_compute_engine.config_manager.file_utils')
  def testWriteConfigLocked(self, mock_lock):
    ioerror = IOError('Test Error')
    mock_lock.LockFile.side_effect = ioerror
    mock_open = mock.mock_open()
    with mock.patch('%s.open' % builtin, mock_open, create=False):
      with self.assertRaises(IOError) as error:
        self.mock_config_manager.WriteConfig()
      self.assertEqual(error.exception, ioerror)
      mock_open().write.assert_not_called()
    mock_lock.LockFile.assert_called_once_with('/var/lock/google_test.lock')


if __name__ == '__main__':
  unittest.main()
