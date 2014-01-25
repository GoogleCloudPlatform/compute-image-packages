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

import json
import logging
import time
import urllib2


ATTRIBUTES_URL = (
    'http://metadata/computeMetadata/v1/project/attributes/?recursive=true&%s')
ACCOUNTS_URL = (
    'http://metadata/computeMetadata/v1/project/attributes/sshKeys?%s')
WAIT_FOR_CHANGE = 'wait_for_change=true&last_etag=%s&timeout_sec=%s'


def AccountDataToDictionary(data):
  """Given sshKeys attribute data, construct a usermap.

  Args:
    data: The data returned from the metadata server's sshKeys attribute.

  Returns:
    A map of {'username': ssh_keys_list}.
  """
  lines = [line for line in data.splitlines() if line]
  usermap = {}
  for line in lines:
    split_line = line.split(':', 1)
    if len(split_line) != 2:
      logging.warning(
          'sshKey is not a complete entry: %s', split_line)
      continue
    user, key = split_line
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
    self.ssh_keys_etag = 0

  def _MakeHangingGetRequest(self, url, etag=0, timeout_secs=300):
    """Makes a get request for the url and specifies wait_for_change.
    """
    wait_for_change_query = WAIT_FOR_CHANGE % (etag, timeout_secs)
    request_url = url % wait_for_change_query
    logging.debug('Getting url: %s', request_url)
    request = urllib2.Request(request_url)
    request.add_header('X-Google-Metadata-Request', 'True')
    return self.urllib2.urlopen(request)

  def _WaitForSshKeysAttribute(self, timeout_secs=600):
    """Waits for sshKeys attribute to be created.

    Returns:
      true if the sshKeys attribute exists, or else false.
    """
    logging.debug('Checking if sshKeys attribute exists.')
    etag = 0
    start_time = self.time.time()
    while self.time.time() - start_time < timeout_secs:
      try:
        response = self._MakeHangingGetRequest(
            ATTRIBUTES_URL, etag=etag)
        response_info = response.info()
        if response_info and response_info.has_key('etag'):
          etag = response_info.getheader('etag')
        attributes_string = response.read()
        logging.debug('project attributes: %s', attributes_string)
        attributes = json.loads(attributes_string)
        if attributes and attributes.has_key('sshKeys'):
          return True
      except (urllib2.URLError, ValueError) as e:
        logging.warning(
            'Error while trying to fetch attributes list: %s',
            e)
    logging.debug('Unable to find sshKeys attribute')
    return False

  def GetDesiredAccounts(self):
    """Get a list of the accounts desired on the system.

    Returns:
      A dict of the form: {'username': ['sshkey1, 'sshkey2', ...]}.
    """
    logging.debug('Getting desired accounts from metadata.')
    try:
      self._WaitForSshKeysAttribute()
      response = self._MakeHangingGetRequest(
          ACCOUNTS_URL,
          etag=self.ssh_keys_etag)
      account_data = response.read()
      if response.info() and response.info().has_key('etag'):
        self.ssh_keys_etag = response.info().getheader('etag')
      if not account_data:
        return {}
      return AccountDataToDictionary(account_data)
    except urllib2.URLError as e:
      logging.debug('error while trying to fetch accounts: %s', e)
    return {}  # No desired accounts at this time.
