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

import logging
import time
import urllib2

ACCOUNTS_URL = (
    'http://metadata.google.internal/0.1/meta-data/attributes/sshKeys')


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

  def GetDesiredAccounts(self):
    """Get a list of the accounts desired on the system.

    Returns:
      A dict of the form: {'username': ['sshkey1, 'sshkey2', ...]}.
    """
    logging.debug('Getting desired accounts from metadata.')
    attempt_failures = []
    start_time = self.time.time()
    while self.time.time() - start_time < 10:  # Try for 10 seconds.
      try:
        logging.debug('Getting SSH Accounts from {0}'.format(ACCOUNTS_URL))
        account_data = self.urllib2.urlopen(
            urllib2.Request(ACCOUNTS_URL)).read()
        if attempt_failures:
          logging.warning(
              'Encountered %s failures when fetching desired accounts: %s',
              len(attempt_failures), attempt_failures)
        if not account_data:
          return {}
        return AccountDataToDictionary(account_data)
      except urllib2.URLError as e:
        attempt_failures.append(e)
      self.time.sleep(0.5)
    logging.warning('Could not fetch accounts from metadata server: %s',
                    attempt_failures)
    return {}  # No desired accounts at this time.
