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

"""Run initialization code the first time the instance boots."""

import logging.handlers
import optparse
import os
import re
import shutil
import subprocess
import tempfile

from google_compute_engine import file_utils
from google_compute_engine import logger
from google_compute_engine import metadata_watcher

from google_compute_engine.boto import boto_config
from google_compute_engine.instance_setup import instance_config


class InstanceSetup(object):
  """Initialize the instance the first time it boots."""

  def __init__(self, debug=False):
    """Constructor.

    Args:
      debug: bool, True if debug output should write to the console.
    """
    self.debug = debug
    facility = logging.handlers.SysLogHandler.LOG_DAEMON
    self.logger = logger.Logger(
        name='instance-setup', debug=self.debug, facility=facility)
    self.watcher = metadata_watcher.MetadataWatcher(logger=self.logger)
    self.metadata_dict = None
    self.instance_config = instance_config.InstanceConfig(logger=self.logger)

    if self.instance_config.GetOptionBool('InstanceSetup', 'network_enabled'):
      self.metadata_dict = self.watcher.GetMetadata()
      instance_config_metadata = self._GetInstanceConfig()
      self.instance_config = instance_config.InstanceConfig(
          logger=self.logger, instance_config_metadata=instance_config_metadata)
      if self.instance_config.GetOptionBool('InstanceSetup', 'set_host_keys'):
        self._SetSshHostKeys()
      if self.instance_config.GetOptionBool('InstanceSetup', 'set_boto_config'):
        self._SetupBotoConfig()
    if self.instance_config.GetOptionBool(
        'InstanceSetup', 'optimize_local_ssd'):
      self._RunScript('optimize_local_ssd')
    if self.instance_config.GetOptionBool('InstanceSetup', 'set_multiqueue'):
      self._RunScript('set_multiqueue')
    try:
      self.instance_config.WriteConfig()
    except (IOError, OSError) as e:
      self.logger.warning(str(e))

  def _GetInstanceConfig(self):
    """Get the instance configuration specified in metadata.

    Returns:
      string, the instance configuration data.
    """
    try:
      instance_data = self.metadata_dict['instance']['attributes']
    except KeyError:
      instance_data = {}
      self.logger.warning('Instance attributes were not found.')

    try:
      project_data = self.metadata_dict['project']['attributes']
    except KeyError:
      project_data = {}
      self.logger.warning('Project attributes were not found.')

    return (instance_data.get('google-instance-configs') or
            project_data.get('google-instance-configs'))

  def _RunScript(self, script):
    """Run a script and log the streamed script output.

    Args:
      script: string, the file location of an executable script.
    """
    process = subprocess.Popen(
        script, shell=True, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
    while True:
      for line in iter(process.stdout.readline, b''):
        self.logger.info(line.decode('utf-8').rstrip('\n'))
      if process.poll() is not None:
        break

  def _GetInstanceId(self):
    """Get the instance ID for this VM.

    Returns:
      string, the instance ID for the VM.
    """
    try:
      return str(self.metadata_dict['instance']['id'])
    except KeyError:
      self.logger.warning('Instance ID was not found in metadata.')
      return None

  def _GenerateSshKey(self, key_type, key_dest):
    """Generate a new SSH key.

    Args:
      key_type: string, the type of the SSH key.
      key_dest: string, a file location to store the SSH key.
    """
    # Create a temporary file to save the created RSA keys.
    with tempfile.NamedTemporaryFile(prefix=key_type, delete=True) as temp:
      temp_key = temp.name

    command = ['ssh-keygen', '-t', key_type, '-f', temp_key, '-N', '', '-q']
    try:
      self.logger.info('Generating SSH key %s.', key_dest)
      subprocess.check_call(command)
    except subprocess.CalledProcessError:
      self.logger.warning('Could not create SSH key %s.', key_dest)
      return

    shutil.move(temp_key, key_dest)
    shutil.move('%s.pub' % temp_key, '%s.pub' % key_dest)

    file_utils.SetPermissions(key_dest, mode=0o600)
    file_utils.SetPermissions('%s.pub' % key_dest, mode=0o644)

  def _StartSshd(self):
    """Initialize the SSH daemon."""
    # Exit as early as possible.
    # Instance setup systemd scripts block sshd from starting.
    if os.path.exists('/bin/systemctl'):
      return
    elif (os.path.exists('/etc/init.d/ssh') or
          os.path.exists('/etc/init/ssh.conf')):
      subprocess.call(['service', 'ssh', 'start'])
      subprocess.call(['service', 'ssh', 'reload'])
    elif (os.path.exists('/etc/init.d/sshd') or
          os.path.exists('/etc/init/sshd.conf')):
      subprocess.call(['service', 'sshd', 'start'])
      subprocess.call(['service', 'sshd', 'reload'])

  def _SetSshHostKeys(self):
    """Regenerates SSH host keys when the VM is restarted with a new IP address.

    Booting a VM from an image with a known SSH key allows a number of attacks.
    This function will regenerating the host key whenever the IP address
    changes. This applies the first time the instance is booted, and each time
    the disk is used to boot a new instance.
    """
    section = 'Instance'
    instance_id = self._GetInstanceId()
    if instance_id != self.instance_config.GetOptionString(
        section, 'instance_id'):
      self.logger.info('Generating SSH host keys for instance %s.', instance_id)
      file_regex = re.compile(r'ssh_host_(?P<type>[a-z0-9]*)_key\Z')
      key_dir = '/etc/ssh'
      key_files = [f for f in os.listdir(key_dir) if file_regex.match(f)]
      for key_file in key_files:
        key_type = file_regex.match(key_file).group('type')
        key_dest = os.path.join(key_dir, key_file)
        self._GenerateSshKey(key_type, key_dest)
      self._StartSshd()
      self.instance_config.SetOption(section, 'instance_id', str(instance_id))

  def _GetNumericProjectId(self):
    """Get the numeric project ID.

    Returns:
      string, the numeric project ID.
    """
    try:
      return str(self.metadata_dict['project']['numericProjectId'])
    except KeyError:
      self.logger.warning('Numeric project ID was not found in metadata.')
      return None

  def _SetupBotoConfig(self):
    """Set the boto config so GSUtil works with provisioned service accounts."""
    project_id = self._GetNumericProjectId()
    try:
      boto_config.BotoConfig(project_id, debug=self.debug)
    except (IOError, OSError) as e:
      self.logger.warning(str(e))


def main():
  parser = optparse.OptionParser()
  parser.add_option(
      '-d', '--debug', action='store_true', dest='debug',
      help='print debug output to the console.')
  (options, _) = parser.parse_args()
  InstanceSetup(debug=bool(options.debug))


if __name__ == '__main__':
  main()
