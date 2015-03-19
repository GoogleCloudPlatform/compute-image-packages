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


METADATA_V1_URL_PREFIX = 'http://169.254.169.254/computeMetadata/v1/'
ATTRIBUTES_URL = METADATA_V1_URL_PREFIX + '?recursive=true&%s'
INSTANCE_SSHKEYS_URL = (
    METADATA_V1_URL_PREFIX + 'instance/attributes/sshKeys?%s')
PROJECT_SSHKEYS_URL = (
    METADATA_V1_URL_PREFIX + 'project/attributes/sshKeys?%s')
WAIT_FOR_CHANGE = 'wait_for_change=true&last_etag=%s&timeout_sec=%s'


def KeyHasExpired(key):
  """ Check to see whether an SSH key has expired.

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
    timestamp in the past, or False otherwise."""

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

  try:
    expire_time = datetime.datetime.strptime(expire_str,
                                             '%Y-%m-%dT%H:%M:%S+0000')
  except ValueError:
    logging.error(
        'Expiration timestamp "%s" not in format %Y-%m-%dT%H:%M:%S+0000.',
        expire_str)
    logging.error('Not expiring key.')
    return False

  # Expire the key if and only if we have exceeded the expiration timestamp.
  return (datetime.datetime.utcnow() > expire_time)


def AccountDataToDictionary(data):
  """Given sshKeys attribute data, construct a usermap.

  Args:
    data: The data returned from the metadata server's sshKeys attribute.

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
          'sshKey is not a complete entry: %s', split_line)
      continue
    user, key = split_line
    if KeyHasExpired(key):
      logging.debug(
          'Skipping expired SSH key for user %s: %s', user, key)
      continue
    if not user in usermap:
      usermap[user] = []
    usermap[user].append(key)
  logging.debug('User accounts: {0}'.format(usermap))
  return usermap


class DesiredAccounts(object):
  """Interface to determine the accounts desired on this instance."""

  def __init__(self, time_module=time, urllib2_module=urllib2):
    self.urllib2 = urllib2_module
    self.time = time_module
    self.attributes_etag = 0
    self.instance_sshkeys_etag = 0

  def _MakeHangingGetRequest(self, url, etag, timeout_secs):
    """Makes a get request for the url and specifies wait_for_change.
    """
    wait_for_change_query = WAIT_FOR_CHANGE % (etag, timeout_secs)
    request_url = url % wait_for_change_query
    logging.debug('Getting url: %s', request_url)
    request = urllib2.Request(request_url)
    request.add_header('Metadata-Flavor', 'Google')
    return self.urllib2.urlopen(request, timeout=timeout_secs*1.1)

  def _GetAttribute(self,
                   attribute_url,
                   etag=0,
                   timeout_secs=60):
    """Fetches the attribute available at the attribute_url.

    Args:
      attribute_url: The url to fetch. It must have a place holder where the
          query with etag, and timeout can be specified to allow hanging gets.
      etag: The etag to use when making the query. Don't specify if you want
          the get to return immediately.
      timeout_secs: The timeout in seconds.

    Returns:
      Tuple containing the string value of attribute and new etag.
      If attribute doesn't exist, None.
    """
    try:
      response = self._MakeHangingGetRequest(
          attribute_url, etag=etag, timeout_secs=timeout_secs)
      response_info = response.info()
      if response_info and response_info.has_key('etag'):
        etag = response_info.getheader('etag')
      attribute_value = response.read()
      logging.debug('response: %s', attribute_value)
      return (attribute_value, etag)
    except urllib2.HTTPError as e:
      if e.code == 404:
        # The attribute doesn't exist. Return None.
        # No need to log a warning.
        return None
      # rethrow the exception since we don't know what it is. Let the
      # top layer handle it
      raise
    return None

  def GetDesiredAccounts(self):
    """Get a list of the accounts desired on the system.

    Returns:
      A dict of the form: {'username': ['sshkey1, 'sshkey2', ...]}.
    """
    logging.debug('Getting desired accounts from metadata.')
    # Fetch the top level attribute with a hanging get
    attribute_data = self._GetAttribute(
        ATTRIBUTES_URL,
        etag=self.attributes_etag)
    if attribute_data:
      # Store the project level attributes etag value. If
      # we are able to successfully fetch the attributes we will
      # update the class member with this value.
      attributes_etag_cache = attribute_data[1]

    # Something has changed. Assume it is the sshKeys. This is not
    # ideal, however, given that metadata updates are not common
    # making this assumption simplifies the code complexity.
    #
    # sshKeys attribute can exist in either the instance attributes
    # collection or the project attributes collection. If it is present
    # in the instance attributes collection, then that value is used
    # and the project level value is ignored.
    # Check if instance attributes collection has sshKeys attribute.
    # We can run this call as a hanging get since if the instance
    # level attribute exists we can ignore any changes to the project
    # level key.
    attribute_data = self._GetAttribute(
        INSTANCE_SSHKEYS_URL,
        etag = self.instance_sshkeys_etag)
    if attribute_data:
      logging.debug('Found instance sshKeys attribute.')
      # There is an sshKeys attribute on the instance. Use it
      account_data = attribute_data[0]
      self.instance_sshkeys_etag = attribute_data[1]
    else:
      # Fetch the sshKeys attribute from project collection. We cannot
      # use a hanging get here since it is possible this call may take
      # a long time and during that the instance metadata can change which
      # we will miss.
      logging.debug(
          'Instance sshKeys attribute not found. Falling back to project')
      attribute_data = self._GetAttribute(PROJECT_SSHKEYS_URL)
      if attribute_data:
        logging.debug('Project sshKeys attribute found.')
        # There is an sshKeys attribute. Use it
        account_data = attribute_data[0]
      else:
        logging.debug('Project sshKeys attribute not found.')
        # sshKeys doesn't exist for either project or instance.
        account_data = None

    self.attributes_etag = attributes_etag_cache
    return AccountDataToDictionary(account_data)
