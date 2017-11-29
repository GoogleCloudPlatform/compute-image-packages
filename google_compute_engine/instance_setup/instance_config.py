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

"""A library used to set up the instance's default configurations file.

Note that the configurations in
/etc/default/instance_configs.cfg.template override the values set in
/etc/default/instance_configs.cfg. The system instance_configs.cfg may be
overridden during package upgrade.
"""

import logging
import os

from google_compute_engine import config_manager
from google_compute_engine import constants
from google_compute_engine.compat import parser
from google_compute_engine.compat import stringio


class InstanceConfig(config_manager.ConfigManager):
  """Creates a defaults config file for instance configuration."""

  instance_config = constants.SYSCONFDIR + '/instance_configs.cfg'
  instance_config_distro = '%s.distro' % instance_config
  instance_config_template = '%s.template' % instance_config
  instance_config_script = os.path.abspath(__file__)
  instance_config_header = (
      'This file is automatically created at boot time by the %s script. Do '
      'not edit this file directly. If you need to add items to this file, '
      'create or edit %s instead and then run '
      '/usr/bin/google_instance_setup.')
  instance_config_options = {
      'Accounts': {
          'deprovision_remove': 'false',
          'groups': 'adm,dip,docker,lxd,plugdev,video',

          # The encrypted password is set to '*' for SSH on Linux systems
          # without PAM.
          #
          # SSH uses '!' as its locked account token:
          # https://github.com/openssh/openssh-portable/blob/master/configure.ac
          #
          # When the token is specified, SSH denies login:
          # https://github.com/openssh/openssh-portable/blob/master/auth.c
          #
          # To solve the issue, make the password '*' which is also recognized
          # as locked but does not prevent SSH login.
          'groupadd_cmd': 'groupadd {group}',
          'useradd_cmd': 'useradd -m -s /bin/bash -p * {user}',
          'userdel_cmd': 'userdel -r {user}',
          'usermod_cmd': 'usermod -G {groups} {user}',
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
          'host_key_types': 'ecdsa,ed25519,rsa',
          'optimize_local_ssd': 'true',
          'network_enabled': 'true',
          'set_boto_config': 'true',
          'set_host_keys': 'true',
          'set_multiqueue': 'true',
      },
      'IpForwarding': {
          'ethernet_proto_id': '66',
          'ip_aliases': 'true',
          'target_instance_ips': 'true',
      },
      'MetadataScripts': {
          'run_dir': '',
          'startup': 'true',
          'shutdown': 'true',
      },
      'NetworkInterfaces': {
          'setup': 'true',
          'dhclient_script': '/sbin/google-dhclient-script',
          'dhcp_command': '',
      },
  }

  def __init__(self, logger=logging, instance_config_metadata=None):
    """Constructor.

    Inherit from the ConfigManager class. Read the template for instance
    defaults and write new sections and options. This prevents package
    updates from overriding user set defaults.

    Args:
      logger: logger object, used to write to SysLog and serial port.
      instance_config_metadata: string, a config file specified in metadata.
    """
    self.logger = logger
    self.instance_config_metadata = instance_config_metadata
    self.instance_config_header %= (
        self.instance_config_script, self.instance_config_template)
    # User provided instance configs should always take precedence.
    super(InstanceConfig, self).__init__(
        config_file=self.instance_config_template,
        config_header=self.instance_config_header)

    # Use the instance config settings from metadata if specified. Then use
    # settings in an instance config file if one exists. If a config
    # file does not already exist, try to use the distro provided defaults. If
    # no file exists, use the default configuration settings.
    config_files = [self.instance_config, self.instance_config_distro]
    config_defaults = []
    if self.instance_config_metadata:
      config = parser.SafeConfigParser()
      try:
        config.readfp(stringio.StringIO(self.instance_config_metadata))
      except parser.Error as e:
        self.logger.error('Error parsing metadata configs: %s', str(e))
      else:
        config_defaults.append(
            dict((s, dict(config.items(s))) for s in config.sections()))
    for config_file in config_files:
      if os.path.exists(config_file):
        config = parser.SafeConfigParser()
        try:
          config.read(config_file)
        except parser.Error as e:
          self.logger.error('Error parsing config file: %s', str(e))
        else:
          config_defaults.append(
              dict((s, dict(config.items(s))) for s in config.sections()))
    config_defaults.append(self.instance_config_options)

    for defaults in config_defaults:
      for section, options in sorted(defaults.items()):
        for option, value in sorted(options.items()):
          super(InstanceConfig, self).SetOption(
              section, option, value, overwrite=False)

  def WriteConfig(self):
    """Write the config values to the instance defaults file."""
    super(InstanceConfig, self).WriteConfig(config_file=self.instance_config)
