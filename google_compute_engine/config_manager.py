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

"""A library for retrieving and modifying configuration settings."""

import textwrap

from google_compute_engine import file_utils
from google_compute_engine.compat import parser

CONFIG = '/etc/default/instance_configs.cfg'
LOCKFILE = '/var/lock/google_config_manager.lock'


class ConfigManager(object):
  """Process the configuration defaults."""

  def __init__(self, config_file=None, config_header=None, config_options=None):
    """Constructor.

    Args:
      config_file: string, the location of the config file.
      config_header: string, the message to write at the top of the config.
      config_options: dict, a map from options to its section in the config.
    """
    self.config_file = config_file or CONFIG
    self.config_header = config_header
    self.config_options = config_options or {}
    self.config = parser.SafeConfigParser()
    self.config.read(self.config_file)

  def _AddHeader(self, fp):
    """Create a file header in the config.

    Args:
      fp: int, a file pointer for writing the header.
    """
    text = textwrap.wrap(
        textwrap.dedent(self.config_header), break_on_hyphens=False)
    fp.write('\n'.join(['# ' + line for line in text]))
    fp.write('\n\n')

  def GetOptionString(self, option, section=None):
    """Get the value of an option in the config file.

    Args:
      option: string, the option to retrieve the value of.
      section: string, the section of the config file to check.

    Returns:
      string, the value of the option or None if the option doesn't exist.
    """
    section = section or self.config_options.get(option)
    if self.config.has_option(section, option):
      return self.config.get(section, option)
    else:
      return None

  def GetOptionBool(self, option, section=None):
    """Get the value of an option in the config file.

    Args:
      option: string, the option to retrieve the value of.
      section: string, the section of the config file to check.

    Returns:
      bool, True if the option is enabled.
    """
    section = section or self.config_options.get(option)
    return (self.config.has_option(section, option) and
            self.config.getboolean(section, option))

  def SetOption(self, option, value, section=None):
    """Set the value of an option in the config file.

    Args:
      option: string, the option to set the value of.
      value: string, the value to set the option.
      section: string, the section of the config file to check.
    """
    section = section or self.config_options.get(option)
    if not self.config.has_section(section):
      self.config.add_section(section)
    self.config.set(section, option, str(value))

  def WriteConfig(self, config_file=None):
    """Write the config values to a given file.

    Args:
      config_file: string, the file location of the config file to write.
    """
    config_file = config_file or self.config_file
    with file_utils.LockFile(LOCKFILE):
      with open(config_file, 'w') as config:
        if self.config_header:
          self._AddHeader(config)
        self.config.write(config)
