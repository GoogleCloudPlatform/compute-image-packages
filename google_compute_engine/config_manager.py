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

import os
import textwrap

from google_compute_engine import file_utils
from google_compute_engine.compat import parser

CONFIG = '/etc/default/instance_configs.cfg'


class ConfigManager(object):
  """Process the configuration defaults."""

  def __init__(self, config_file=None, config_header=None):
    """Constructor.

    Args:
      config_file: string, the location of the config file.
      config_header: string, the message to write at the top of the config.
    """
    self.config_file = config_file or CONFIG
    self.config_header = config_header
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

  def GetOptionString(self, section, option):
    """Get the value of an option in the config file.

    Args:
      section: string, the section of the config file to check.
      option: string, the option to retrieve the value of.

    Returns:
      string, the value of the option or None if the option doesn't exist.
    """
    if self.config.has_option(section, option):
      return self.config.get(section, option)
    else:
      return None

  def GetOptionBool(self, section, option):
    """Get the value of an option in the config file.

    Args:
      section: string, the section of the config file to check.
      option: string, the option to retrieve the value of.

    Returns:
      bool, True if the option is enabled or not set.
    """
    return (not self.config.has_option(section, option) or
            self.config.getboolean(section, option))

  def SetOption(self, section, option, value, overwrite=True):
    """Set the value of an option in the config file.

    Args:
      section: string, the section of the config file to check.
      option: string, the option to set the value of.
      value: string, the value to set the option.
      overwrite: bool, True to overwrite an existing value in the config file.
    """
    if not overwrite and self.config.has_option(section, option):
      return
    if not self.config.has_section(section):
      self.config.add_section(section)
    self.config.set(section, option, str(value))

  def WriteConfig(self, config_file=None):
    """Write the config values to a given file.

    Args:
      config_file: string, the file location of the config file to write.
    """
    config_file = config_file or self.config_file
    config_name = os.path.splitext(os.path.basename(config_file))[0]
    config_lock = '/var/lock/google_%s.lock' % config_name
    with file_utils.LockFile(config_lock):
      with open(config_file, 'w') as config_fp:
        if self.config_header:
          self._AddHeader(config_fp)
        self.config.write(config_fp)
