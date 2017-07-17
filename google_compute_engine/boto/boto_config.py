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

"""A library used to set up the system boto.cfg file.

If a project ID is not provided, this request the project ID from the
metadata server and install the compute authentication plugin.

Note the config starts with the content in /etc/boto.cfg.template,
overrides settings, and then persists it into /etc/boto.cfg. This
is done so that the system boto.cfg can be removed prior to image
packaging.
"""

import os

from google_compute_engine import config_manager
from google_compute_engine import constants
from google_compute_engine import logger
from google_compute_engine import metadata_watcher


class BotoConfig(object):
  """Creates a boto config file for standalone GSUtil."""

  boto_config = constants.BOTOCONFDIR + '/etc/boto.cfg'
  boto_config_template = constants.BOTOCONFDIR + '/etc/boto.cfg.template'
  boto_config_script = os.path.abspath(__file__)
  boto_config_header = (
      'This file is automatically created at boot time by the %s script. Do '
      'not edit this file directly. If you need to add items to this file, '
      'create or edit %s instead and then re-run the script.')

  def __init__(self, project_id=None, debug=False):
    """Constructor.

    Args:
      project_id: string, the project ID to use in the config file.
      debug: bool, True if debug output should write to the console.
    """
    self.logger = logger.Logger(name='boto-setup', debug=debug)
    self.watcher = metadata_watcher.MetadataWatcher(logger=self.logger)
    self._CreateConfig(project_id)

  def _GetNumericProjectId(self):
    """Get the numeric project ID for this VM.

    Returns:
      string, the numeric project ID if one is found.
    """
    project_id = 'project/numeric-project-id'
    return self.watcher.GetMetadata(metadata_key=project_id, recursive=False)

  def _CreateConfig(self, project_id):
    """Create the boto config to support standalone GSUtil.

    Args:
      project_id: string, the project ID to use in the config file.
    """
    project_id = project_id or self._GetNumericProjectId()

    # Our project doesn't support service accounts.
    if not project_id:
      return

    self.boto_config_header %= (
        self.boto_config_script, self.boto_config_template)
    config = config_manager.ConfigManager(
        config_file=self.boto_config_template,
        config_header=self.boto_config_header)
    boto_dir = os.path.dirname(self.boto_config_script)

    config.SetOption('GSUtil', 'default_project_id', project_id)
    config.SetOption('GSUtil', 'default_api_version', '2')
    config.SetOption('GoogleCompute', 'service_account', 'default')
    config.SetOption('Plugin', 'plugin_directory', boto_dir)
    config.WriteConfig(config_file=self.boto_config)
