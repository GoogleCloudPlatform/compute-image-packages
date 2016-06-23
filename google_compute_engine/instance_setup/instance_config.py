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

"""A library used to set up the instance defaults file.

Note that this starts with whatever is in
/etc/defaults/instance_config.cfg.template and then persists it into
/etc/defaults/instance_config.cfg. This is done so that the system
instance_config.cfg can be removed prior to image packaging.
"""

import os

from google_compute_engine import config_manager
from google_compute_engine.compat import parser


class InstanceConfig(config_manager.ConfigManager):
  """Creates a defaults config file for instance configuration."""

  instance_config = '/etc/default/instance_configs.cfg'
  instance_config_distro = '%s.distro' % instance_config
  instance_config_template = '%s.template' % instance_config
  instance_config_script = os.path.abspath(__file__)
  instance_config_header = (
      'This file is automatically created at boot time by the %s script. Do '
      'not edit this file directly. If you need to add items to this file, '
      'create or edit %s instead and then re-run the script.')
  instance_config_options = {
      'Accounts': {
          'deprovision_remove': 'false',
          'groups': 'adm,dip,lxd,plugdev,video',
      },
      'Daemons': {
          'accounts_daemon': 'true',
          'clock_skew_daemon': 'true',
          'ip_forwarding_daemon': 'true',
      },
      'Instance': {
          'instance_id': '0',
      },
      'InstanceSetup': {
          'optimize_local_ssd': 'true',
          'network_enabled': 'true',
          'set_boto_config': 'true',
          'set_host_keys': 'true',
          'set_multiqueue': 'true',
      },
      'IpForwarding': {
          'ethernet_proto_id': '66',
      },
      'MetadataScripts': {
          'startup': 'true',
          'shutdown': 'true',
      },
  }

  def __init__(self):
    """Constructor.

    Inherit from the ConfigManager class. Read the template for instance
    defaults and write new sections and options. This prevents package
    updates from overriding user set defaults.
    """
    self.instance_config_header %= (
        self.instance_config_script, self.instance_config_template)
    # User provided instance configs should always take precedence.
    super(InstanceConfig, self).__init__(
        config_file=self.instance_config_template,
        config_header=self.instance_config_header)

    # Use the settings in an instance config file if one exists. If a config
    # file does not already exist, try to use the distro provided defaults. If
    # no file exists, use the default configuration settings.
    if os.path.exists(self.instance_config):
      instance_config = self.instance_config
    elif os.path.exists(self.instance_config_distro):
      instance_config = self.instance_config_distro
    else:
      instance_config = None

    if instance_config:
      config = parser.SafeConfigParser()
      config.read(instance_config)
      defaults = dict((s, dict(config.items(s))) for s in config.sections())
    else:
      defaults = self.instance_config_options

    for section, options in sorted(defaults.items()):
      for option, value in sorted(options.items()):
        super(InstanceConfig, self).SetOption(
            section, option, value, overwrite=False)

  def WriteConfig(self):
    """Write the config values to the instance defaults file."""
    super(InstanceConfig, self).WriteConfig(config_file=self.instance_config)
