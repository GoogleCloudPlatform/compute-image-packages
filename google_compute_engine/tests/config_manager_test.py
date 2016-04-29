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

import unittest

from google_compute_engine import config_manager
import mock


class ConfigManagerTest(unittest.TestCase):

  option = 'option'
  section = 'section'
  value = 'value'
  config_options = {option: section}

  def HasOption(self, section, _):
    """Validate the option has a section in the config file.

    Args:
      section: string, the section of the config associated with the option.

    Returns:
      bool, True if section exists.
    """
    return bool(section)

  def HasSection(self, section):
    """Validate the section exists when setting the config file.

    Args:
      section: string, the section of the config file to check.

    Returns:
      bool, True if an option maps to the section in the config file.
    """
    return section in self.config_options.values()

  def setUp(self):
    self.mock_config = mock.Mock()
    self.mock_config.has_option.side_effect = self.HasOption
    self.mock_config.has_section.side_effect = self.HasSection
    config_manager.parser.SafeConfigParser = mock.Mock()
    config_manager.parser.SafeConfigParser.return_value = self.mock_config

    self.config_file = 'test.cfg'
    self.config_header = 'Config file header.'

    self.mock_config_manager = config_manager.ConfigManager(
        config_file=self.config_file, config_header=self.config_header,
        config_options=self.config_options)

  def testAddHeader(self):
    mock_fp = mock.Mock()
    self.mock_config_manager._AddHeader(mock_fp)
    expected_calls = [
        mock.call('# %s' % self.config_header),
        mock.call('\n\n'),
    ]
    self.assertEqual(mock_fp.write.mock_calls, expected_calls)

  def testGetOptionString(self):
    self.mock_config_manager.GetOptionString(option=self.option)
    expected_calls = [
        mock.call.read(self.config_file),
        mock.call.has_option(self.section, self.option),
        mock.call.get(self.section, self.option),
    ]
    self.assertEqual(self.mock_config.mock_calls, expected_calls)

  def testGetOptionStringWithSection(self):
    option = 'test-option'
    section = 'test-section'
    self.mock_config_manager.GetOptionString(option=option, section=section)
    expected_calls = [
        mock.call.read(self.config_file),
        mock.call.has_option(section, option),
        mock.call.get(section, option),
    ]
    self.assertEqual(self.mock_config.mock_calls, expected_calls)

  def testGetOptionStringNoSection(self):
    option = 'test-option'
    self.assertIsNone(self.mock_config_manager.GetOptionString(option=option))
    expected_calls = [
        mock.call.read(self.config_file),
        mock.call.has_option(None, option),
    ]
    self.assertEqual(self.mock_config.mock_calls, expected_calls)

  def testGetOptionBool(self):
    self.mock_config_manager.GetOptionBool(option=self.option)
    expected_calls = [
        mock.call.read(self.config_file),
        mock.call.has_option(self.section, self.option),
        mock.call.getboolean(self.section, self.option),
    ]
    self.assertEqual(self.mock_config.mock_calls, expected_calls)

  def testGetOptionBoolWithSection(self):
    option = 'test-option'
    section = 'test-section'
    self.mock_config_manager.GetOptionBool(option=option, section=section)
    expected_calls = [
        mock.call.read(self.config_file),
        mock.call.has_option(section, option),
        mock.call.getboolean(section, option),
    ]
    self.assertEqual(self.mock_config.mock_calls, expected_calls)

  def testGetOptionBoolNoSection(self):
    option = 'test-option'
    self.assertFalse(self.mock_config_manager.GetOptionBool(option=option))
    expected_calls = [
        mock.call.read(self.config_file),
        mock.call.has_option(None, option),
    ]
    self.assertEqual(self.mock_config.mock_calls, expected_calls)

  def testSetOption(self):
    self.mock_config_manager.SetOption(option=self.option, value=self.value)
    expected_calls = [
        mock.call.read(self.config_file),
        mock.call.has_section(self.section),
        mock.call.set(self.section, self.option, self.value),
    ]
    self.assertEqual(self.mock_config.mock_calls, expected_calls)

  def testSetOptionNewSection(self):
    section = 'test-section'
    self.mock_config_manager.SetOption(
        option=self.option, value=self.value, section=section)
    expected_calls = [
        mock.call.read(self.config_file),
        mock.call.has_section(section),
        mock.call.add_section(section),
        mock.call.set(section, self.option, self.value),
    ]
    self.assertEqual(self.mock_config.mock_calls, expected_calls)

  def testWriteConfig(self):
    mock_open = mock.mock_open()
    with mock.patch('__builtin__.open', mock_open, create=False):
      self.mock_config_manager.WriteConfig()
      expected_calls = [
          mock.call('# %s' % self.config_header),
          mock.call('\n\n'),
      ]
      self.assertEqual(mock_open().write.mock_calls, expected_calls)

  def testWriteConfigNoHeader(self):
    self.mock_config_manager = config_manager.ConfigManager(
        config_file=self.config_file)
    mock_open = mock.mock_open()
    with mock.patch('__builtin__.open', mock_open, create=False):
      self.mock_config_manager.WriteConfig()
      mock_open().write.assert_not_called()

  @mock.patch('google_compute_engine.config_manager.lock_file')
  def testWriteConfigLocked(self, mock_lock):
    ioerror = IOError('Test Error')
    mock_lock.LockFile.side_effect = ioerror
    mock_open = mock.mock_open()
    with mock.patch('__builtin__.open', mock_open, create=False):
      with self.assertRaises(IOError) as error:
        self.mock_config_manager.WriteConfig()
      self.assertEqual(error.exception, ioerror)
      mock_open().write.assert_not_called()


if __name__ == '__main__':
  unittest.main()
