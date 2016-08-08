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

"""Execute user provided metadata scripts."""

import os
import stat
import subprocess


class ScriptExecutor(object):
  """A class for executing user provided metadata scripts."""

  def __init__(self, logger, script_type):
    """Constructor.

    Args:
      logger: logger object, used to write to SysLog and serial port.
      script_type: string, the type of the script we are running.
    """
    self.logger = logger
    self.script_type = script_type

  def _MakeExecutable(self, metadata_script):
    """Add executable permissions to a file.

    Args:
      metadata_script: string, the path to the executable file.
    """
    mode = os.stat(metadata_script).st_mode
    os.chmod(metadata_script, mode | stat.S_IEXEC)

  def _RunScript(self, metadata_key, metadata_script):
    """Run a script and log the streamed script output.

    Args:
      metadata_key: string, the key specifing the metadata script.
      metadata_script: string, the file location of an executable script.
    """
    process = subprocess.Popen(
        metadata_script, shell=True, executable='/bin/bash',
        stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
    while True:
      for line in iter(process.stdout.readline, b''):
        message = line.decode('utf-8', 'replace').rstrip('\n')
        if message:
          self.logger.info('%s: %s', metadata_key, message)
      if process.poll() is not None:
        break
    self.logger.info('%s: Return code %s.', metadata_key, process.returncode)

  def RunScripts(self, script_dict):
    """Run the metadata scripts; execute a URL script first if one is provided.

    Args:
      script_dict: a dictionary mapping metadata keys to script files.
    """
    metadata_types = ['%s-script-url', '%s-script']
    metadata_keys = [key % self.script_type for key in metadata_types]
    metadata_keys = [key for key in metadata_keys if script_dict.get(key)]
    if not metadata_keys:
      self.logger.info('No %s scripts found in metadata.', self.script_type)
    for metadata_key in metadata_keys:
      metadata_script = script_dict.get(metadata_key)
      self._MakeExecutable(metadata_script)
      self._RunScript(metadata_key, metadata_script)
