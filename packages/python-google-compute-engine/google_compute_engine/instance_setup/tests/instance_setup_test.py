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

"""Unittest for instance_setup.py module."""

import subprocess

from google_compute_engine.instance_setup import instance_setup
from google_compute_engine.test_compat import builtin
from google_compute_engine.test_compat import mock
from google_compute_engine.test_compat import unittest


class InstanceSetupTest(unittest.TestCase):

  def setUp(self):
    self.mock_instance_config = mock.Mock()
    self.mock_logger = mock.Mock()
    self.mock_setup = mock.create_autospec(instance_setup.InstanceSetup)
    self.mock_setup.debug = False
    self.mock_setup.instance_config = self.mock_instance_config
    self.mock_setup.logger = self.mock_logger

  @mock.patch('google_compute_engine.instance_setup.instance_setup.instance_config')
  @mock.patch('google_compute_engine.instance_setup.instance_setup.metadata_watcher')
  @mock.patch('google_compute_engine.instance_setup.instance_setup.logger')
  def testInstanceSetup(self, mock_logger, mock_watcher, mock_config):
    mock_setup = mock.create_autospec(instance_setup.InstanceSetup)
    mocks = mock.Mock()
    mocks.attach_mock(mock_logger, 'logger')
    mocks.attach_mock(mock_watcher, 'watcher')
    mocks.attach_mock(mock_config, 'config')
    mocks.attach_mock(mock_setup, 'setup')
    mock_logger_instance = mock.Mock()
    mock_logger.Logger.return_value = mock_logger_instance
    mock_watcher_instance = mock.Mock()
    mock_watcher_instance.GetMetadata.return_value = {'hello': 'world'}
    mock_watcher.MetadataWatcher.return_value = mock_watcher_instance
    mock_config_instance = mock.Mock()
    mock_config_instance.GetOptionBool.return_value = True
    mock_config_instance.GetOptionString.return_value = 'type'
    mock_config.InstanceConfig.return_value = mock_config_instance
    mock_setup._GetInstanceConfig.return_value = 'config'

    instance_setup.InstanceSetup.__init__(mock_setup)
    expected_calls = [
        # Setup and reading the configuration file.
        mock.call.logger.Logger(
            name=mock.ANY, debug=False, facility=mock.ANY),
        mock.call.watcher.MetadataWatcher(logger=mock_logger_instance),
        mock.call.config.InstanceConfig(logger=mock_logger_instance),
        # Check network access for reaching the metadata server.
        mock.call.config.InstanceConfig().GetOptionBool(
            'InstanceSetup', 'network_enabled'),
        mock.call.watcher.MetadataWatcher().GetMetadata(),
        # Get the instance config if specified in metadata.
        mock.call.setup._GetInstanceConfig(),
        mock.call.config.InstanceConfig(
            logger=mock_logger_instance, instance_config_metadata='config'),
        # Setup for SSH host keys if necessary.
        mock.call.config.InstanceConfig().GetOptionBool(
            'InstanceSetup', 'set_host_keys'),
        mock.call.config.InstanceConfig().GetOptionString(
            'InstanceSetup', 'host_key_types'),
        mock.call.setup._SetSshHostKeys(host_key_types='type'),
        # Setup for the boto config if necessary.
        mock.call.config.InstanceConfig().GetOptionBool(
            'InstanceSetup', 'set_boto_config'),
        mock.call.setup._SetupBotoConfig(),
        # Setup for local SSD.
        mock.call.config.InstanceConfig().GetOptionBool(
            'InstanceSetup', 'optimize_local_ssd'),
        mock.call.setup._RunScript('google_optimize_local_ssd'),
        # Setup for multiqueue virtio driver.
        mock.call.config.InstanceConfig().GetOptionBool(
            'InstanceSetup', 'set_multiqueue'),
        mock.call.setup._RunScript('google_set_multiqueue'),
        # Write the updated config file.
        mock.call.config.InstanceConfig().WriteConfig(),
    ]
    self.assertEqual(mocks.mock_calls, expected_calls)
    self.assertEqual(mock_setup.metadata_dict, {'hello': 'world'})

  @mock.patch('google_compute_engine.instance_setup.instance_setup.instance_config')
  @mock.patch('google_compute_engine.instance_setup.instance_setup.metadata_watcher')
  @mock.patch('google_compute_engine.instance_setup.instance_setup.logger')
  def testInstanceSetupException(self, mock_logger, mock_watcher, mock_config):
    mock_setup = mock.create_autospec(instance_setup.InstanceSetup)
    mocks = mock.Mock()
    mocks.attach_mock(mock_logger, 'logger')
    mocks.attach_mock(mock_watcher, 'watcher')
    mocks.attach_mock(mock_config, 'config')
    mocks.attach_mock(mock_setup, 'setup')
    mock_logger_instance = mock.Mock()
    mock_logger.Logger.return_value = mock_logger_instance
    mock_config_instance = mock.Mock()
    mock_config_instance.GetOptionBool.return_value = False
    mock_config_instance.WriteConfig.side_effect = IOError('Test Error')
    mock_config.InstanceConfig.return_value = mock_config_instance

    instance_setup.InstanceSetup.__init__(mock_setup)
    expected_calls = [
        mock.call.logger.Logger(
            name=mock.ANY, debug=False, facility=mock.ANY),
        mock.call.watcher.MetadataWatcher(logger=mock_logger_instance),
        mock.call.config.InstanceConfig(logger=mock_logger_instance),
        mock.call.config.InstanceConfig().GetOptionBool(
            'InstanceSetup', 'network_enabled'),
        mock.call.config.InstanceConfig().GetOptionBool(
            'InstanceSetup', 'optimize_local_ssd'),
        mock.call.config.InstanceConfig().GetOptionBool(
            'InstanceSetup', 'set_multiqueue'),
        mock.call.config.InstanceConfig().WriteConfig(),
        mock.call.logger.Logger().warning('Test Error'),
    ]
    self.assertEqual(mocks.mock_calls, expected_calls)
    self.assertIsNone(mock_setup.metadata_dict)

  def testGetInstanceConfig(self):
    instance_config = 'test'
    self.mock_setup.metadata_dict = {
        'instance': {
            'attributes': {
                'google-instance-configs': instance_config,
            }
        },
        'project': {
            'attributes': {
                'google-instance-configs': 'Unused config.',
            }
        }
    }
    self.assertEqual(
        instance_setup.InstanceSetup._GetInstanceConfig(self.mock_setup),
        instance_config)
    self.mock_logger.warning.assert_not_called()

  def testGetInstanceConfigProject(self):
    instance_config = 'test'
    self.mock_setup.metadata_dict = {
        'instance': {
            'attributes': {}
        },
        'project': {
            'attributes': {
                'google-instance-configs': instance_config,
            }
        }
    }
    self.assertEqual(
        instance_setup.InstanceSetup._GetInstanceConfig(self.mock_setup),
        instance_config)
    self.mock_logger.warning.assert_not_called()

  def testGetInstanceConfigNone(self):
    self.mock_setup.metadata_dict = {
        'instance': {
            'attributes': {}
        },
        'project': {
            'attributes': {}
        }
    }
    self.assertIsNone(
        instance_setup.InstanceSetup._GetInstanceConfig(self.mock_setup))
    self.mock_logger.warning.assert_not_called()

  def testGetInstanceConfigNoMetadata(self):
    self.mock_setup.metadata_dict = {}
    self.assertIsNone(
        instance_setup.InstanceSetup._GetInstanceConfig(self.mock_setup))
    self.assertEqual(self.mock_logger.warning.call_count, 2)

  @mock.patch('google_compute_engine.instance_setup.instance_setup.subprocess')
  def testRunScript(self, mock_subprocess):
    mock_readline = mock.Mock()
    mock_readline.side_effect = [bytes(b'a\n'), bytes(b'b\n'), bytes(b'')]
    mock_stdout = mock.Mock()
    mock_stdout.readline = mock_readline
    mock_process = mock.Mock()
    mock_process.poll.return_value = 0
    mock_process.stdout = mock_stdout
    mock_subprocess.Popen.return_value = mock_process
    script = '/tmp/script.py'

    instance_setup.InstanceSetup._RunScript(self.mock_setup, script)
    expected_calls = [mock.call('a'), mock.call('b')]
    self.assertEqual(self.mock_logger.info.mock_calls, expected_calls)
    mock_subprocess.Popen.assert_called_once_with(
        script, shell=True, stderr=mock_subprocess.STDOUT,
        stdout=mock_subprocess.PIPE)
    mock_process.poll.assert_called_once_with()

  def testGetInstanceId(self):
    self.mock_setup.metadata_dict = {'instance': {'attributes': {}, 'id': 123}}
    self.assertEqual(
        instance_setup.InstanceSetup._GetInstanceId(self.mock_setup), '123')
    self.mock_logger.warning.assert_not_called()

  def testGetInstanceIdNotFound(self):
    self.mock_setup.metadata_dict = {'instance': {'attributes': {}}}
    self.assertIsNone(
        instance_setup.InstanceSetup._GetInstanceId(self.mock_setup))
    self.assertEqual(self.mock_logger.warning.call_count, 1)

  @mock.patch('google_compute_engine.instance_setup.instance_setup.file_utils.SetPermissions')
  @mock.patch('google_compute_engine.instance_setup.instance_setup.shutil.move')
  @mock.patch('google_compute_engine.instance_setup.instance_setup.subprocess.check_call')
  @mock.patch('google_compute_engine.instance_setup.instance_setup.tempfile.NamedTemporaryFile')
  def testGenerateSshKey(
      self, mock_tempfile, mock_call, mock_move, mock_permissions):
    mocks = mock.Mock()
    mocks.attach_mock(mock_tempfile, 'tempfile')
    mocks.attach_mock(mock_call, 'call')
    mocks.attach_mock(mock_move, 'move')
    mocks.attach_mock(mock_permissions, 'permissions')
    mocks.attach_mock(self.mock_logger, 'logger')
    key_type = 'key-type'
    key_dest = '/key/dest'
    temp_dest = '/tmp/dest'
    mock_tempfile.return_value = mock_tempfile
    mock_tempfile.__enter__.return_value.name = temp_dest
    mock_open = mock.mock_open()
    key_file_contents = 'ssh-rsa asdfasdf'
    expected_key_data = ('ssh-rsa', 'asdfasdf')

    with mock.patch('%s.open' % builtin, mock_open, create=False):
      mock_open().read.return_value = key_file_contents
      key_data = instance_setup.InstanceSetup._GenerateSshKey(
          self.mock_setup, key_type, key_dest)
      expected_calls = [
          mock.call.tempfile(prefix=key_type, delete=True),
          mock.call.tempfile.__enter__(),
          mock.call.tempfile.__exit__(None, None, None),
          mock.call.logger.info(mock.ANY, key_dest),
          mock.call.call(
              ['ssh-keygen', '-t', key_type, '-f', temp_dest, '-N', '', '-q']),
          mock.call.move(temp_dest, key_dest),
          mock.call.move('%s.pub' % temp_dest, '%s.pub' % key_dest),
          mock.call.permissions(key_dest, mode=0o600),
          mock.call.permissions('%s.pub' % key_dest, mode=0o644),
      ]
      self.assertEqual(mocks.mock_calls, expected_calls)
      self.assertEqual(key_data, expected_key_data)

      mock_open().read.return_value = ''
      key_data = instance_setup.InstanceSetup._GenerateSshKey(
          self.mock_setup, key_type, key_dest)
      self.assertEqual(key_data, None)

  @mock.patch('google_compute_engine.instance_setup.instance_setup.subprocess.check_call')
  def testGenerateSshKeyProcessError(self, mock_call):
    key_type = 'key-type'
    key_dest = '/key/dest'
    mock_call.side_effect = subprocess.CalledProcessError(1, 'Test')

    instance_setup.InstanceSetup._GenerateSshKey(
        self.mock_setup, key_type, key_dest)
    self.mock_logger.info.assert_called_once_with(mock.ANY, key_dest)
    self.mock_logger.warning.assert_called_once_with(mock.ANY, key_dest)

  @mock.patch('google_compute_engine.instance_setup.instance_setup.subprocess.call')
  @mock.patch('google_compute_engine.instance_setup.instance_setup.os.path.exists')
  def testStartSshdSysVinit(self, mock_exists, mock_call):
    mocks = mock.Mock()
    mocks.attach_mock(mock_exists, 'exists')
    mocks.attach_mock(mock_call, 'call')
    mock_exists.side_effect = [False, False, True]

    instance_setup.InstanceSetup._StartSshd(self.mock_setup)
    expected_calls = [
        mock.call.exists('/bin/systemctl'),
        mock.call.exists('/etc/init.d/ssh'),
        mock.call.exists('/etc/init/ssh.conf'),
        mock.call.call(['service', 'ssh', 'start']),
        mock.call.call(['service', 'ssh', 'reload']),
    ]
    self.assertEqual(mocks.mock_calls, expected_calls)

  @mock.patch('google_compute_engine.instance_setup.instance_setup.subprocess.call')
  @mock.patch('google_compute_engine.instance_setup.instance_setup.os.path.exists')
  def testStartSshdUpstart(self, mock_exists, mock_call):
    mocks = mock.Mock()
    mocks.attach_mock(mock_exists, 'exists')
    mocks.attach_mock(mock_call, 'call')
    mock_exists.side_effect = [False, False, False, False, True]

    instance_setup.InstanceSetup._StartSshd(self.mock_setup)
    expected_calls = [
        mock.call.exists('/bin/systemctl'),
        mock.call.exists('/etc/init.d/ssh'),
        mock.call.exists('/etc/init/ssh.conf'),
        mock.call.exists('/etc/init.d/sshd'),
        mock.call.exists('/etc/init/sshd.conf'),
        mock.call.call(['service', 'sshd', 'start']),
        mock.call.call(['service', 'sshd', 'reload']),
    ]
    self.assertEqual(mocks.mock_calls, expected_calls)

  @mock.patch('google_compute_engine.instance_setup.instance_setup.subprocess.call')
  @mock.patch('google_compute_engine.instance_setup.instance_setup.os.path.exists')
  def testStartSshdSystemd(self, mock_exists, mock_call):
    mocks = mock.Mock()
    mocks.attach_mock(mock_exists, 'exists')
    mocks.attach_mock(mock_call, 'call')
    mock_exists.return_value = True

    instance_setup.InstanceSetup._StartSshd(self.mock_setup)
    expected_calls = [mock.call.exists('/bin/systemctl')]
    self.assertEqual(mocks.mock_calls, expected_calls)

  def testSetSshHostKeys(self):
    self.mock_instance_config.GetOptionString.return_value = '123'
    mock_instance_id = mock.Mock()
    mock_instance_id.return_value = '123'
    self.mock_setup._GetInstanceId = mock_instance_id

    instance_setup.InstanceSetup._SetSshHostKeys(self.mock_setup)
    self.mock_instance_config.SetOption.assert_not_called()

  @mock.patch('google_compute_engine.instance_setup.instance_setup.urlrequest.urlopen')
  @mock.patch('google_compute_engine.instance_setup.instance_setup.PutRequest')
  def testWriteHostKeyToGuestAttributes(self, mock_put, mock_urlopen):
    key_type = 'ssh-rsa'
    key_value = 'asdfasdf'
    encoded_key_value = key_value.encode('utf-8')
    expected_url = ('http://metadata.google.internal/computeMetadata/v1/'
                    'instance/guest-attributes/hostkeys/%s' % key_type)
    headers = {'Metadata-Flavor': 'Google'}

    instance_setup.InstanceSetup._WriteHostKeyToGuestAttributes(
        self.mock_setup, key_type, key_value)
    self.mock_logger.info.assert_called_with(
        'Wrote %s host key to guest attributes.', key_type)
    mock_put.assert_called_with(expected_url, encoded_key_value, headers)

    mock_urlopen.side_effect = instance_setup.urlerror.HTTPError(
        'http://foo', 403, 'Forbidden', {}, None)
    instance_setup.InstanceSetup._WriteHostKeyToGuestAttributes(
        self.mock_setup, key_type, key_value)
    self.mock_logger.info.assert_called_with(
        'Unable to write %s host key to guest attributes.', key_type)

  def testPutRequest(self):
    put_request = instance_setup.PutRequest('http://example.com/')
    self.assertEqual(put_request.get_method(), 'PUT')

  @mock.patch('google_compute_engine.instance_setup.instance_setup.os.listdir')
  def testSetSshHostKeysFirstBoot(self, mock_listdir):
    self.mock_instance_config.GetOptionString.return_value = None
    mock_instance_id = mock.Mock()
    mock_instance_id.return_value = '123'
    self.mock_setup._GetInstanceId = mock_instance_id
    mock_generate_key = mock.Mock()
    mock_generate_key.return_value = ('ssh-rsa', 'asdfasdf')
    self.mock_setup._GenerateSshKey = mock_generate_key
    mock_listdir.return_value = [
        'ssh_config',
        'ssh_host_dsa_key',
        'ssh_host_dsa_key.pub',
        'ssh_host_ed25519_key',
        'ssh_host_ed25519_key.pub',
        'ssh_host_rsa_key',
        'ssh_host_rsa_key.pub',
    ]

    instance_setup.InstanceSetup._SetSshHostKeys(
        self.mock_setup, host_key_types='rsa,dsa,abc')
    expected_calls = [
        mock.call('abc', '/etc/ssh/ssh_host_abc_key'),
        mock.call('dsa', '/etc/ssh/ssh_host_dsa_key'),
        mock.call('ed25519', '/etc/ssh/ssh_host_ed25519_key'),
        mock.call('rsa', '/etc/ssh/ssh_host_rsa_key'),
    ]

    self.assertEqual(sorted(mock_generate_key.mock_calls), expected_calls)
    self.mock_instance_config.SetOption.assert_called_once_with(
        'Instance', 'instance_id', '123')

  def testGetNumericProjectId(self):
    self.mock_setup.metadata_dict = {
        'project': {
            'attributes': {},
            'numericProjectId': 123,
        }
    }
    self.assertEqual(
        instance_setup.InstanceSetup._GetNumericProjectId(self.mock_setup),
        '123')
    self.mock_logger.warning.assert_not_called()

  def testGetNumericProjectIdNotFound(self):
    self.mock_setup.metadata_dict = {'project': {'attributes': {}}}
    self.assertIsNone(
        instance_setup.InstanceSetup._GetNumericProjectId(self.mock_setup))
    self.assertEqual(self.mock_logger.warning.call_count, 1)

  @mock.patch('google_compute_engine.instance_setup.instance_setup.boto_config.BotoConfig')
  def testSetupBotoConfig(self, mock_boto):
    mock_project_id = mock.Mock()
    mock_project_id.return_value = '123'
    self.mock_setup._GetNumericProjectId = mock_project_id
    instance_setup.InstanceSetup._SetupBotoConfig(self.mock_setup)
    mock_boto.assert_called_once_with('123', debug=False)

  @mock.patch('google_compute_engine.instance_setup.instance_setup.boto_config.BotoConfig')
  def testSetupBotoConfigLocked(self, mock_boto):
    mock_boto.side_effect = IOError('Test Error')
    instance_setup.InstanceSetup._SetupBotoConfig(self.mock_setup)
    self.mock_logger.warning.assert_called_once_with('Test Error')


if __name__ == '__main__':
  unittest.main()
