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

"""Unittest for metadata_watcher.py module."""

import os

from google_compute_engine import metadata_watcher
from google_compute_engine.test_compat import mock
from google_compute_engine.test_compat import unittest


class MetadataWatcherTest(unittest.TestCase):

  def setUp(self):
    self.mock_logger = mock.Mock()
    self.timeout = 60
    self.url = 'http://metadata.google.internal/computeMetadata/v1'
    self.params = {
        'alt': 'json',
        'last_etag': 0,
        'recursive': True,
        'timeout_sec': self.timeout,
        'wait_for_change': True,
    }
    self.mock_watcher = metadata_watcher.MetadataWatcher(
        logger=self.mock_logger, timeout=self.timeout)

  @mock.patch('google_compute_engine.metadata_watcher.urlrequest.build_opener')
  @mock.patch('google_compute_engine.metadata_watcher.urlrequest.ProxyHandler')
  @mock.patch('google_compute_engine.metadata_watcher.urlrequest.Request')
  def testGetMetadataRequest(self, mock_request, mock_proxy, mock_opener):
    mock_open = mock.Mock()
    mock_handler = mock.Mock()
    mock_response = mock.Mock()
    mocks = mock.Mock()
    mocks.attach_mock(mock_request, 'request')
    mocks.attach_mock(mock_proxy, 'proxy')
    mocks.attach_mock(mock_handler, 'handler')
    mocks.attach_mock(mock_opener, 'opener')
    mocks.attach_mock(mock_open, 'open')
    mocks.attach_mock(mock_response, 'response')
    mock_request.return_value = mock_request
    mock_proxy.return_value = mock_handler
    mock_opener.return_value = mock_open
    mock_response.getcode.return_value = metadata_watcher.httpclient.OK
    mock_open.open.return_value = mock_response
    params = {'hello': 'world'}
    request_url = '%s?hello=world' % self.url
    headers = {'Metadata-Flavor': 'Google'}
    timeout = self.timeout * 1.1

    self.mock_watcher._GetMetadataRequest(self.url, params=params)
    expected_calls = [
        mock.call.request(request_url, headers=headers),
        mock.call.proxy({}),
        mock.call.opener(mock_handler),
        mock.call.open.open(mock_request, timeout=timeout),
        mock.call.response.getcode(),
    ]
    self.assertEqual(mocks.mock_calls, expected_calls)

  @mock.patch('google_compute_engine.metadata_watcher.time')
  @mock.patch('google_compute_engine.metadata_watcher.urlrequest.build_opener')
  @mock.patch('google_compute_engine.metadata_watcher.urlrequest.ProxyHandler')
  @mock.patch('google_compute_engine.metadata_watcher.urlrequest.Request')
  def testGetMetadataRequestRetry(
      self, mock_request, mock_proxy, mock_opener, mock_time):
    mock_open = mock.Mock()
    mock_handler = mock.Mock()
    mocks = mock.Mock()
    mocks.attach_mock(mock_request, 'request')
    mocks.attach_mock(mock_proxy, 'proxy')
    mocks.attach_mock(mock_handler, 'handler')
    mocks.attach_mock(mock_opener, 'opener')
    mocks.attach_mock(mock_open, 'open')
    mocks.attach_mock(mock_time, 'time')
    mock_request.return_value = mock_request
    mock_proxy.return_value = mock_handler
    mock_opener.return_value = mock_open

    mock_unavailable = mock.Mock()
    mock_unavailable.getcode.return_value = (
        metadata_watcher.httpclient.SERVICE_UNAVAILABLE)
    mock_timeout = metadata_watcher.socket.timeout('Test timeout')
    mock_success = mock.Mock()
    mock_success.getcode.return_value = metadata_watcher.httpclient.OK

    # Retry after a service unavailable error response.
    mock_open.open.side_effect = [
        metadata_watcher.StatusException(mock_unavailable),
        mock_timeout,
        mock_success,
    ]
    request_url = '%s?' % self.url
    headers = {'Metadata-Flavor': 'Google'}
    timeout = self.timeout * 1.1

    self.mock_watcher._GetMetadataRequest(self.url)
    expected_calls = [
        mock.call.request(request_url, headers=headers),
        mock.call.proxy({}),
        mock.call.opener(mock_handler),
        mock.call.open.open(mock_request, timeout=timeout),
        mock.call.time.sleep(mock.ANY),
        mock.call.request(request_url, headers=headers),
        mock.call.proxy({}),
        mock.call.opener(mock_handler),
        mock.call.open.open(mock_request, timeout=timeout),
        mock.call.time.sleep(mock.ANY),
        mock.call.request(request_url, headers=headers),
        mock.call.proxy({}),
        mock.call.opener(mock_handler),
        mock.call.open.open(mock_request, timeout=timeout),
    ]
    self.assertEqual(mocks.mock_calls, expected_calls)

  @mock.patch('google_compute_engine.metadata_watcher.time')
  @mock.patch('google_compute_engine.metadata_watcher.urlrequest.build_opener')
  @mock.patch('google_compute_engine.metadata_watcher.urlrequest.ProxyHandler')
  @mock.patch('google_compute_engine.metadata_watcher.urlrequest.Request')
  def testGetMetadataRequestHttpException(
      self, mock_request, mock_proxy, mock_opener, mock_time):
    mock_open = mock.Mock()
    mock_handler = mock.Mock()
    mock_response = mock.Mock()
    mock_request.return_value = mock_request
    mock_proxy.return_value = mock_handler
    mock_opener.return_value = mock_open
    mock_response.getcode.return_value = metadata_watcher.httpclient.NOT_FOUND
    mock_open.open.side_effect = metadata_watcher.StatusException(mock_response)

    with self.assertRaises(metadata_watcher.StatusException):
      self.mock_watcher._GetMetadataRequest(self.url)
    self.assertEqual(mock_request.call_count, 1)
    self.assertEqual(mock_proxy.call_count, 1)
    self.assertEqual(mock_opener.call_count, 1)
    self.assertEqual(mock_open.open.call_count, 1)
    self.assertEqual(mock_response.getcode.call_count, 1)

  @mock.patch('google_compute_engine.metadata_watcher.urlrequest.build_opener')
  @mock.patch('google_compute_engine.metadata_watcher.urlrequest.ProxyHandler')
  @mock.patch('google_compute_engine.metadata_watcher.urlrequest.Request')
  def testGetMetadataRequestException(
      self, mock_request, mock_proxy, mock_opener):
    mock_open = mock.Mock()
    mock_handler = mock.Mock()
    mock_response = mock.Mock()
    mock_request.return_value = mock_request
    mock_proxy.return_value = mock_handler
    mock_opener.return_value = mock_open
    mock_response.getcode.return_value = metadata_watcher.httpclient.NOT_FOUND
    mock_open.open.side_effect = mock_response

    with self.assertRaises(metadata_watcher.StatusException):
      self.mock_watcher._GetMetadataRequest(self.url)
    self.assertEqual(mock_request.call_count, 1)
    self.assertEqual(mock_proxy.call_count, 1)
    self.assertEqual(mock_opener.call_count, 1)
    self.assertEqual(mock_open.open.call_count, 1)

  def testUpdateEtag(self):
    mock_response = mock.Mock()
    mock_response.headers = {'etag': 1}
    self.assertEqual(self.mock_watcher.etag, 0)

    # Update the etag if the etag is set.
    self.assertTrue(self.mock_watcher._UpdateEtag(mock_response))
    self.assertEqual(self.mock_watcher.etag, 1)

    # Do not update the etag if the etag is unchanged.
    self.assertFalse(self.mock_watcher._UpdateEtag(mock_response))
    self.assertEqual(self.mock_watcher.etag, 1)

    # Do not update the etag if the etag is not set.
    mock_response.headers = {}
    self.assertFalse(self.mock_watcher._UpdateEtag(mock_response))
    self.assertEqual(self.mock_watcher.etag, 1)

  def testGetMetadataUpdate(self):
    mock_response = mock.Mock()
    mock_response.return_value = mock_response
    mock_response.headers = {'etag': 1}
    mock_response.read.return_value = bytes(b'{}')
    self.mock_watcher._GetMetadataRequest = mock_response
    request_url = os.path.join(self.url, '')

    self.assertEqual(self.mock_watcher._GetMetadataUpdate(), {})
    self.assertEqual(self.mock_watcher.etag, 1)
    mock_response.assert_called_once_with(
        request_url, params=self.params, timeout=None)

  def testGetMetadataUpdateArgs(self):
    mock_response = mock.Mock()
    mock_response.return_value = mock_response
    mock_response.headers = {'etag': 0}
    mock_response.read.return_value = bytes(b'{}')
    self.mock_watcher._GetMetadataRequest = mock_response
    metadata_key = 'instance/id'
    self.params['recursive'] = False
    self.params['wait_for_change'] = False
    request_url = os.path.join(self.url, metadata_key)

    self.mock_watcher._GetMetadataUpdate(
        metadata_key=metadata_key, recursive=False, wait=False, timeout=60)
    self.assertEqual(self.mock_watcher.etag, 0)
    mock_response.assert_called_once_with(
        request_url, params=self.params, timeout=60)

  def testGetMetadataUpdateWait(self):
    self.params['last_etag'] = 1
    self.mock_watcher.etag = 1
    mock_unchanged = mock.Mock()
    mock_unchanged.headers = {'etag': 1}
    mock_unchanged.read.return_value = bytes(b'{}')
    mock_changed = mock.Mock()
    mock_changed.headers = {'etag': 2}
    mock_changed.read.return_value = bytes(b'{}')
    mock_response = mock.Mock()
    mock_response.side_effect = [mock_unchanged, mock_unchanged, mock_changed]
    self.mock_watcher._GetMetadataRequest = mock_response
    request_url = os.path.join(self.url, '')

    self.mock_watcher._GetMetadataUpdate()
    self.assertEqual(self.mock_watcher.etag, 2)
    expected_calls = [
        mock.call(request_url, params=self.params, timeout=None),
    ] * 3
    self.assertEqual(mock_response.mock_calls, expected_calls)

  def testHandleMetadataUpdate(self):
    mock_response = mock.Mock()
    mock_response.return_value = {}
    self.mock_watcher._GetMetadataUpdate = mock_response

    self.assertEqual(self.mock_watcher.GetMetadata(), {})
    mock_response.assert_called_once_with(
        metadata_key='', recursive=True, wait=False, timeout=None)
    self.mock_watcher.logger.exception.assert_not_called()

  def testHandleMetadataUpdateException(self):
    mock_response = mock.Mock()
    first = metadata_watcher.socket.timeout()
    second = metadata_watcher.urlerror.URLError('Test')
    mock_response.side_effect = [first, first, second, {}]
    self.mock_watcher._GetMetadataUpdate = mock_response
    metadata_key = 'instance/id'
    recursive = False
    wait = False
    retries = 5

    self.assertEqual(
        self.mock_watcher._HandleMetadataUpdate(
            metadata_key=metadata_key, recursive=recursive, wait=wait,
            timeout=None, retries=retries),
        {})
    expected_calls = [
        mock.call(
          metadata_key=metadata_key, recursive=recursive, wait=wait,
          timeout=None),
    ] * 4
    self.assertEqual(mock_response.mock_calls, expected_calls)
    expected_calls = [mock.call.error(mock.ANY, mock.ANY)] * 2
    self.assertEqual(self.mock_logger.mock_calls, expected_calls)

  def testHandleMetadataUpdateExceptionNoRetry(self):
    mock_response = mock.Mock()
    mock_response.side_effect = metadata_watcher.socket.timeout()
    self.mock_watcher._GetMetadataUpdate = mock_response
    metadata_key = 'instance/id'
    recursive = False
    wait = False
    retries = 0

    self.assertIsNone(
        self.mock_watcher._HandleMetadataUpdate(
            metadata_key=metadata_key, recursive=recursive, wait=wait,
            timeout=None, retries=retries))
    expected_calls = [
        mock.call(
            metadata_key=metadata_key, recursive=recursive, wait=wait,
            timeout=None),
    ]
    self.assertEqual(mock_response.mock_calls, expected_calls)
    expected_calls = [mock.call.error(mock.ANY, mock.ANY)]
    self.assertEqual(self.mock_logger.mock_calls, expected_calls)

  def testWatchMetadata(self):
    mock_response = mock.Mock()
    mock_response.return_value = {}
    self.mock_watcher._HandleMetadataUpdate = mock_response
    mock_handler = mock.Mock()
    mock_handler.side_effect = Exception()
    self.mock_logger.exception.side_effect = RuntimeError()
    recursive = True

    with self.assertRaises(RuntimeError):
      self.mock_watcher.WatchMetadata(mock_handler, recursive=recursive)
    mock_handler.assert_called_once_with({})
    mock_response.assert_called_once_with(
        metadata_key='', recursive=recursive, wait=True, timeout=None)

  def testWatchMetadataException(self):
    mock_response = mock.Mock()
    mock_response.side_effect = metadata_watcher.socket.timeout()
    self.mock_watcher._GetMetadataUpdate = mock_response
    self.mock_logger.error.side_effect = RuntimeError()
    metadata_key = 'instance/id'
    recursive = False

    with self.assertRaises(RuntimeError):
      self.mock_watcher.WatchMetadata(
          None, metadata_key=metadata_key, recursive=recursive)
    mock_response.assert_called_once_with(
        metadata_key=metadata_key, recursive=recursive, wait=True, timeout=None)

  def testGetMetadata(self):
    mock_response = mock.Mock()
    mock_response.return_value = {}
    self.mock_watcher._HandleMetadataUpdate = mock_response

    self.assertEqual(self.mock_watcher.GetMetadata(), {})
    mock_response.assert_called_once_with(
        metadata_key='', recursive=True, wait=False, timeout=None, retries=5)
    self.mock_watcher.logger.exception.assert_not_called()

  def testGetMetadataArgs(self):
    mock_response = mock.Mock()
    mock_response.return_value = {}
    self.mock_watcher._HandleMetadataUpdate = mock_response
    metadata_key = 'instance/id'
    recursive = False
    retries = 5

    response = self.mock_watcher.GetMetadata(
        metadata_key=metadata_key, recursive=recursive, timeout=60,
        retries=retries)
    self.assertEqual(response, {})
    mock_response.assert_called_once_with(
        metadata_key=metadata_key, recursive=False, wait=False, timeout=60,
        retries=5)
    self.mock_watcher.logger.exception.assert_not_called()


if __name__ == '__main__':
  unittest.main()
