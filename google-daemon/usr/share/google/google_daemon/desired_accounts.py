#!/usr/bin/python
# Copyright 2013 Google Inc. All Rights Reserved.
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

"""Get the accounts desired to be present on the VM."""

import datetime
import json
import logging
import time
import urllib2


METADATA_URL = 'http://metadata.google.internal/computeMetadata/v1'
METADATA_HANG = ('/?recursive=true&alt=json&wait_for_change=true'
                 '&timeout_sec=%s&last_etag=%s')


def KeyHasExpired(key):
  """Check to see whether an SSH key has expired.

  Uses Google-specific (for now) semantics of the OpenSSH public key format's
  comment field to determine if an SSH key is past its expiration timestamp, and
  therefore no longer to be trusted. This format is still subject to change.
  Reliance on it in any way is at your own risk.

  Args:
    key: A single public key entry in OpenSSH public key file format. This will
      be checked for Google-specific comment semantics, and if present, those
      will be analysed.

  Returns:
    True if the key has Google-specific comment semantics and has an expiration
    timestamp in the past, or False otherwise.
  """

  logging.debug('Processing key: %s', key)

  try:
    schema, json_str = key.split(None, 3)[2:]
  except ValueError:
    logging.debug('Key does not seem to have a schema identifier.')
    logging.debug('Not expiring key.')
    return False

  if schema != 'google-ssh':
    logging.debug('Rejecting %s as potential key schema identifier.', schema)
    return False

  logging.debug('Google SSH key schema identifier found.')
  logging.debug('JSON string detected: %s', json_str)

  try:
    json_obj = json.loads(json_str)
  except ValueError:
    logging.error('Invalid JSON. Not expiring key.')
    return False

  if 'expireOn' not in json_obj:
    # Use warning instead of error for this failure mode in case we
    # add future use cases for this JSON which are unrelated to expiration.
    logging.warning('No expiration timestamp. Not expiring key.')
    return False

  expire_str = json_obj['expireOn']
  format_str = '%Y-%m-%dT%H:%M:%S+0000'

  try:
    expire_time = datetime.datetime.strptime(expire_str, format_str)
  except ValueError:
    logging.error(
        'Expiration timestamp "%s" not in format %s.', expire_str, format_str)
    logging.error('Not expiring key.')
    return False

  # Expire the key if and only if we have exceeded the expiration timestamp.
  return datetime.datetime.utcnow() > expire_time


def AccountDataToDictionary(data):
  """Given SSH key data, construct a usermap.

  Args:
    data: The data returned from the metadata server's SSH key attributes.

  Returns:
    A map of {'username': ssh_keys_list}.
  """
  if not data:
    return {}
  lines = [line for line in data.splitlines() if line]
  usermap = {}
  for line in lines:
    split_line = line.split(':', 1)
    if len(split_line) != 2:
      logging.warning(
          'SSH key is not a complete entry: %s', split_line)
      continue
    user, key = split_line
    if KeyHasExpired(key):
      logging.debug(
          'Skipping expired SSH key for user %s: %s', user, key)
      continue
    if user not in usermap:
      usermap[user] = []
    usermap[user].append(key)
  logging.debug('User accounts: %s', usermap)
  return usermap


class DesiredAccounts(object):
  """Interface to determine the accounts desired on this instance."""

  def __init__(self, time_module=time, urllib2_module=urllib2):
    self.urllib2 = urllib2_module
    self.time = time_module
    self.etag = 0

  def _WaitForUpdate(self, timeout_secs):
    """Makes a hanging get request for the contents of the metadata server."""
    request_url = METADATA_URL + METADATA_HANG % (timeout_secs, self.etag)
    logging.debug('Getting url: %s', request_url)
    request = urllib2.Request(request_url)
    request.add_header('Metadata-Flavor', 'Google')
    return self.urllib2.urlopen(request, timeout=timeout_secs*1.1)

  def _GetMetadataUpdate(self, timeout_secs=60):
    """Fetches the content of the metadata server.

    Args:
      timeout_secs: The timeout in seconds.

    Returns:
      The JSON formatted string content of the metadata server.
    """
    try:
      response = self._WaitForUpdate(timeout_secs=timeout_secs)
      response_info = response.info()
      if response_info and response_info.has_key('etag'):
        self.etag = response_info.getheader('etag')
      content = response.read()
      logging.debug('response: %s', content)
      return content
    except urllib2.HTTPError as e:
      if e.code == 404:
        # The metadata server content doesn't exist. Return None.
        # No need to log a warning.
        return None
      # Rethrow the exception since we don't know what it is. Let the
      # top layer handle it.
      raise
    return None

  def GetDesiredAccounts(self):
    """Get a list of the accounts desired on the system.

    Returns:
      A dict of the form: {'username': ['sshkey1, 'sshkey2', ...]}.
    """
    logging.debug('Getting desired accounts from metadata.')
    # Fetch the top level attribute with a hanging get.
    metadata_content = self._GetMetadataUpdate()
    metadata_dict = json.loads(metadata_content or '{}')
    account_data = None

    try:
      instance_data = metadata_dict['instance']['attributes']
      project_data = metadata_dict['project']['attributes']
      # Instance SSH keys to use regardless of project metadata.
      valid_keys = [instance_data.get('sshKeys'), instance_data.get('ssh-keys')]
      block_project = instance_data.get('block-project-ssh-keys', '').lower()
      if block_project != 'true' and not instance_data.get('sshKeys'):
        valid_keys.append(project_data.get('ssh-keys'))
        valid_keys.append(project_data.get('sshKeys'))
      valid_keys = [key for key in valid_keys if key]
      account_data = '\n'.join(valid_keys)
    except KeyError:
      logging.debug('Project or instance attributes were not found.')

    return AccountDataToDictionary(account_data)
