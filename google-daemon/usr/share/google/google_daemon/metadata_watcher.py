#!/usr/bin/python
# Copyright 2015 Google Inc. All Rights Reserved.
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

import httplib
import time
import urllib
import urllib2


METADATA_URL = 'http://metadata.google.internal/computeMetadata/v1/'


class Error(Exception):
  pass


class UnexpectedStatusException(Error):
  pass


class MetadataWatcher(object):
  """Watches for changing metadata."""

  def __init__(self, httplib_module=httplib, time_module=time,
               urllib_module=urllib, urllib2_module=urllib2):
    self.httplib = httplib_module
    self.time = time_module
    self.urllib = urllib_module
    self.urllib2 = urllib2_module

  def WatchMetadataForever(self, metadata_key, handler, initial_value=None):
    """Watches for a change in the value of metadata.

    Args:
      metadata_key: The key identifying which metadata to watch for changes.
      handler: A callable to call when the metadata value changes. Will be passed
        a single parameter, the new value of the metadata.
      initial_value: The expected initial value for the metadata. The handler will
        not be called on the initial metadata request unless the value differs
        from this.

    Raises:
      UnexpectedStatusException: If the http request is unsuccessful for an
        unexpected reason.
    """
    params = {
        'wait_for_change': 'true',
        'last_etag': 0,
        }

    value = initial_value
    while True:
      # start a hanging-GET request for metadata key.
      url = '{base_url}{key}?{params}'.format(
          base_url=METADATA_URL,
          key=metadata_key,
          params=self.urllib.urlencode(params)
          )
      req = self.urllib2.Request(url, headers={'Metadata-Flavor': 'Google'})

      try:
        response = self.urllib2.urlopen(req)
        content = response.read()
        status = response.getcode()
      except self.urllib2.HTTPError as e:
        content = None
        status = e.code

      if status == self.httplib.SERVICE_UNAVAILABLE:
        self.time.sleep(1)
        continue
      elif status == self.httplib.OK:
        # Extract new metadata value and latest etag.
        new_value = content
        headers = response.info()
        params['last_etag'] = headers['ETag']
      else:
        raise UnexpectedStatusException(status)

      # If the metadata value changed, call the appropriate handler.
      if value == initial_value:
        value = new_value
      elif value != new_value:
        value = new_value
        handler(value)
