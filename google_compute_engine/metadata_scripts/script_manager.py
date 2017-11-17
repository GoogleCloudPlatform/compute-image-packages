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

"""Manage the retrieval and excution of metadata scripts."""

import contextlib
import logging.handlers
import optparse
import shutil
import tempfile

from google_compute_engine import config_manager
from google_compute_engine import logger
from google_compute_engine.metadata_scripts import script_executor
from google_compute_engine.metadata_scripts import script_retriever


@contextlib.contextmanager
def _CreateTempDir(prefix, run_dir=None):
  """Context manager for creating a temporary directory.

  Args:
    prefix: string, the prefix for the temporary directory.
    run_dir: string, the base directory location of the temporary directory.

  Yields:
    string, the temporary directory created.
  """
  temp_dir = tempfile.mkdtemp(prefix=prefix + '-', dir=run_dir)
  try:
    yield temp_dir
  finally:
    shutil.rmtree(temp_dir)


class ScriptManager(object):
  """A class for retrieving and executing metadata scripts."""

  def __init__(self, script_type, run_dir=None, debug=False):
    """Constructor.

    Args:
      script_type: string, the metadata script type to run.
      run_dir: string, the base directory location of the temporary directory.
      debug: bool, True if debug output should write to the console.
    """
    self.script_type = script_type
    name = '%s-script' % self.script_type
    facility = logging.handlers.SysLogHandler.LOG_DAEMON
    self.logger = logger.Logger(name=name, debug=debug, facility=facility)
    self.retriever = script_retriever.ScriptRetriever(self.logger, script_type)
    self.executor = script_executor.ScriptExecutor(self.logger, script_type)
    self._RunScripts(run_dir=run_dir)

  def _RunScripts(self, run_dir=None):
    """Retrieve metadata scripts and execute them.

    Args:
      run_dir: string, the base directory location of the temporary directory.
    """
    with _CreateTempDir(self.script_type, run_dir=run_dir) as dest_dir:
      try:
        self.logger.info('Starting %s scripts.', self.script_type)
        script_dict = self.retriever.GetScripts(dest_dir)
        self.executor.RunScripts(script_dict)
      finally:
        self.logger.info('Finished running %s scripts.', self.script_type)


def main():
  script_types = ('startup', 'shutdown')
  parser = optparse.OptionParser()
  parser.add_option(
      '-d', '--debug', action='store_true', dest='debug',
      help='print debug output to the console.')
  parser.add_option(
      '--script-type', dest='script_type', help='metadata script type.')
  (options, _) = parser.parse_args()
  if options.script_type and options.script_type.lower() in script_types:
    script_type = options.script_type.lower()
  else:
    valid_args = ', '.join(script_types)
    message = 'No valid argument specified. Options: [%s].' % valid_args
    raise ValueError(message)

  instance_config = config_manager.ConfigManager()
  if instance_config.GetOptionBool('MetadataScripts', script_type):
    ScriptManager(
        script_type,
        run_dir=instance_config.GetOptionString('MetadataScripts', 'run_dir'),
        debug=bool(options.debug))


if __name__ == '__main__':
  main()
