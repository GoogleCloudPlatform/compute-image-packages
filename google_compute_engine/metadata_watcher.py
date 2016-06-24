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

"""A library for watching changes in the metadata server."""

import functools
import json
import logging
import os
import socket
import time

from google_compute_engine.compat import httpclient
from google_compute_engine.compat import urlerror
from google_compute_engine.compat import urlparse
from google_compute_engine.compat import urlrequest

METADATA_SERVER = 'http://metadata.google.internal/computeMetadata/v1'


class StatusException(urlerror.HTTPError):

  def __init__(self, response):
    url = response.geturl()
    code = response.getcode()
    message = httpclient.responses.get(code)
    headers = response.headers
    super(StatusException, self).__init__(url, code, message, headers, response)


def RetryOnUnavailable(func):
  """Function decorator to retry on a service unavailable exception."""

  @functools.wraps(func)
  def Wrapper(*args, **kwargs):
    while True:
      try:
        response = func(*args, **kwargs)
      except urlerror.HTTPError as e:
        if e.getcode() == httpclient.SERVICE_UNAVAILABLE:
          time.sleep(5)
        else:
          raise
      else:
        if response.getcode() == httpclient.OK:
          return response
        else:
          raise StatusException(response)
  return Wrapper


class MetadataWatcher(object):
  """Watches for changes in metadata."""

  def __init__(self, logger=logging, timeout=60):
    """Constructor.

    Args:
      logger: logger object, used to write to SysLog and serial port.
      timeout: int, timeout in seconds for metadata requests.
    """
    self.etag = 0
    self.logger = logger
    self.timeout = timeout

  @RetryOnUnavailable
  def _GetMetadataRequest(self, metadata_url, params=None):
    """Performs a GET request with the metadata headers.

    Args:
      metadata_url: string, the URL to perform a GET request on.
      params: dictionary, the query parameters in the GET request.

    Returns:
      HTTP response from the GET request.

    Raises:
      urlerror.HTTPError: raises when the GET request fails.
    """
    headers = {'Metadata-Flavor': 'Google'}
    params = urlparse.urlencode(params or {})
    url = '%s?%s' % (metadata_url, params)
    request = urlrequest.Request(url, headers=headers)
    return urlrequest.urlopen(request, timeout=self.timeout*1.1)

  def _UpdateEtag(self, response):
    """Update the etag from an API response.

    Args:
      response: HTTP response with a header field.

    Returns:
      bool, True if the etag in the response header updated.
    """
    etag = response.headers.get('etag', self.etag)
    etag_updated = self.etag != etag
    self.etag = etag
    return etag_updated

  def _GetMetadataUpdate(self, metadata_key='', recursive=True, wait=True):
    """Request the contents of metadata server and deserialize the response.

    Args:
      metadata_key: string, the metadata key to watch for changes.
      recursive: bool, True if we should recursively watch for metadata changes.
      wait: bool, True if we should wait for a metadata change.

    Returns:
      json, the deserialized contents of the metadata server.
    """
    metadata_key = os.path.join(metadata_key, '') if recursive else metadata_key
    metadata_url = os.path.join(METADATA_SERVER, metadata_key)
    params = {
        'alt': 'json',
        'last_etag': self.etag,
        'recursive': recursive,
        'timeout_sec': self.timeout,
        'wait_for_change': wait,
    }
    while True:
      response = self._GetMetadataRequest(metadata_url, params=params)
      etag_updated = self._UpdateEtag(response)
      if wait and not etag_updated:
        # Retry until the etag is updated.
        continue
      else:
        # Waiting for change is not required or the etag is updated.
        break
    return json.loads(response.read().decode('utf-8'))

  def _HandleMetadataUpdate(self, metadata_key='', recursive=True, wait=True):
    """Wait for a successful metadata response.

    Args:
      metadata_key: string, the metadata key to watch for changes.
      recursive: bool, True if we should recursively watch for metadata changes.
      wait: bool, True if we should wait for a metadata change.

    Returns:
      json, the deserialized contents of the metadata server.
    """
    exception = None
    while True:
      try:
        return self._GetMetadataUpdate(
            metadata_key=metadata_key, recursive=recursive, wait=wait)
      except (httpclient.HTTPException, socket.error, urlerror.URLError) as e:
        if isinstance(e, type(exception)) and e.args == exception.args:
          continue
        else:
          exception = e
          message = 'GET request error retrieving metadata. %s.'
          self.logger.exception(message, exception)

  def WatchMetadata(self, handler, metadata_key='', recursive=True):
    """Watch for changes to the contents of the metadata server.

    Args:
      handler: callable, a function to call with the updated metadata contents.
      metadata_key: string, the metadata key to watch for changes.
      recursive: bool, True if we should recursively watch for metadata changes.
    """
    while True:
      response = self._HandleMetadataUpdate(
          metadata_key=metadata_key, recursive=recursive, wait=True)
      try:
        handler(response)
      except Exception as e:
        self.logger.exception('Exception calling the response handler. %s.', e)

  def GetMetadata(self, metadata_key='', recursive=True):
    """Retrieve the contents of metadata server for a metadata key.

    Args:
      metadata_key: string, the metadata key to watch for changes.
      recursive: bool, True if we should recursively watch for metadata changes.

    Returns:
      json, the deserialized contents of the metadata server or None if error.
    """
    return self._HandleMetadataUpdate(
        metadata_key=metadata_key, recursive=recursive, wait=False)
