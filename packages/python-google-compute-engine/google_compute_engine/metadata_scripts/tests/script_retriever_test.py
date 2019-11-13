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

"""Unittest for script_retriever.py module."""

import subprocess

from google_compute_engine.compat import urlerror
from google_compute_engine.metadata_scripts import script_retriever
from google_compute_engine.test_compat import builtin
from google_compute_engine.test_compat import mock
from google_compute_engine.test_compat import unittest


class ScriptRetrieverTest(unittest.TestCase):

  def setUp(self):
    self.script_type = 'test'
    self.dest_dir = '/tmp'
    self.dest = '/tmp/file'
    self.mock_logger = mock.Mock()
    self.mock_watcher = mock.Mock()
    self.retriever = script_retriever.ScriptRetriever(
        self.mock_logger, self.script_type)

  @mock.patch('google_compute_engine.metadata_scripts.script_retriever.tempfile.NamedTemporaryFile')
  @mock.patch('google_compute_engine.metadata_scripts.script_retriever.urlrequest.Request')
  @mock.patch('google_compute_engine.metadata_scripts.script_retriever.urlrequest.urlopen')
  def testDownloadAuthUrl(self, mock_urlopen, mock_request, mock_tempfile):
    auth_url = 'https://storage.googleapis.com/fake/url'
    mock_tempfile.return_value = mock_tempfile
    mock_tempfile.name = self.dest
    self.retriever.token = 'bar'

    mock_open = mock.mock_open()
    with mock.patch('%s.open' % builtin, mock_open):
      self.assertEqual(
          self.retriever._DownloadAuthUrl(auth_url, self.dest_dir), self.dest)

    mock_tempfile.assert_called_once_with(dir=self.dest_dir, delete=False)
    mock_tempfile.close.assert_called_once_with()

    self.mock_logger.info.assert_called_once_with(
        mock.ANY, auth_url, self.dest)
    mock_request.assert_called_with(auth_url)
    mocked_request = mock_request()
    mocked_request.add_unredirected_header.assert_called_with(
        'Authorization', 'bar')
    mock_urlopen.assert_called_with(mocked_request)
    urlopen_read = mock_urlopen().read(return_value=b'foo')
    self.mock_logger.warning.assert_not_called()

    mock_open.assert_called_once_with(self.dest, 'wb')
    handle = mock_open()
    handle.write.assert_called_once_with(urlopen_read)

  @mock.patch('google_compute_engine.metadata_scripts.script_retriever.tempfile.NamedTemporaryFile')
  @mock.patch('google_compute_engine.metadata_scripts.script_retriever.urlrequest.Request')
  @mock.patch('google_compute_engine.metadata_watcher.MetadataWatcher.GetMetadata')
  def testDownloadAuthUrlExceptionAndToken(
      self, mock_get_metadata, mock_request, mock_tempfile):
    auth_url = 'https://storage.googleapis.com/fake/url'
    metadata_prefix = 'http://metadata.google.internal/computeMetadata/v1/'
    token_url = metadata_prefix + 'instance/service-accounts/default/token'
    mock_tempfile.return_value = mock_tempfile
    mock_tempfile.name = self.dest
    self.retriever.token = None

    mock_get_metadata.return_value = {
        'token_type': 'foo', 'access_token': 'bar'}
    mock_request.return_value = mock_request
    mock_request.side_effect = urlerror.URLError('Error.')

    self.assertIsNone(self.retriever._DownloadAuthUrl(auth_url, self.dest_dir))

    mock_get_metadata.return_value = mock_get_metadata
    # GetMetadata includes a prefix, so remove it.
    stripped_url = token_url.replace(metadata_prefix, '')
    mock_get_metadata.assert_called_once_with(
        stripped_url, recursive=False, retries=1)

    self.assertEqual(self.retriever.token, 'foo bar')

    self.mock_logger.info.assert_called_once_with(
        mock.ANY, auth_url, self.dest)
    self.assertEqual(self.mock_logger.warning.call_count, 1)

  @mock.patch('google_compute_engine.metadata_scripts.script_retriever.tempfile.NamedTemporaryFile')
  @mock.patch('google_compute_engine.metadata_scripts.script_retriever.ScriptRetriever._DownloadUrl')
  @mock.patch('google_compute_engine.metadata_watcher.MetadataWatcher.GetMetadata')
  def testDownloadAuthUrlFallback(
      self, mock_get_metadata, mock_download_url, mock_tempfile):
    auth_url = 'https://storage.googleapis.com/fake/url'
    metadata_prefix = 'http://metadata.google.internal/computeMetadata/v1/'
    token_url = metadata_prefix + 'instance/service-accounts/default/token'
    mock_tempfile.return_value = mock_tempfile
    mock_tempfile.name = self.dest
    self.retriever.token = None

    mock_get_metadata.return_value = None
    mock_download_url.return_value = None

    self.assertIsNone(self.retriever._DownloadAuthUrl(auth_url, self.dest_dir))

    mock_get_metadata.return_value = mock_get_metadata
    # GetMetadata includes a prefix, so remove it.
    prefix = 'http://metadata.google.internal/computeMetadata/v1/'
    stripped_url = token_url.replace(prefix, '')
    mock_get_metadata.assert_called_once_with(
        stripped_url, recursive=False, retries=1)
    mock_download_url.assert_called_once_with(auth_url, self.dest_dir)

    self.assertIsNone(self.retriever.token)

    expected_calls = [
        mock.call(mock.ANY, auth_url, self.dest),
        mock.call(mock.ANY),
    ]
    self.assertEqual(self.mock_logger.info.mock_calls, expected_calls)

  @mock.patch('google_compute_engine.metadata_scripts.script_retriever.tempfile.NamedTemporaryFile')
  @mock.patch('google_compute_engine.metadata_scripts.script_retriever.urlretrieve.urlretrieve')
  def testDownloadUrl(self, mock_retrieve, mock_tempfile):
    url = 'http://www.google.com/fake/url'
    mock_tempfile.return_value = mock_tempfile
    mock_tempfile.name = self.dest
    self.assertEqual(
        self.retriever._DownloadUrl(url, self.dest_dir), self.dest)
    mock_tempfile.assert_called_once_with(dir=self.dest_dir, delete=False)
    mock_tempfile.close.assert_called_once_with()
    self.mock_logger.info.assert_called_once_with(mock.ANY, url, self.dest)
    mock_retrieve.assert_called_once_with(url, self.dest)
    self.mock_logger.warning.assert_not_called()

  @mock.patch('google_compute_engine.metadata_scripts.script_retriever.time')
  @mock.patch('google_compute_engine.metadata_scripts.script_retriever.tempfile.NamedTemporaryFile')
  @mock.patch('google_compute_engine.metadata_scripts.script_retriever.urlretrieve.urlretrieve')
  def testDownloadUrlProcessError(self, mock_retrieve, mock_tempfile, mock_time):
    url = 'http://www.google.com/fake/url'
    mock_tempfile.return_value = mock_tempfile
    mock_tempfile.name = self.dest
    mock_success = mock.Mock()
    mock_success.getcode.return_value = script_retriever.httpclient.OK
    # Success after 3 timeout. Since max_retry = 3, the final result is fail.
    mock_retrieve.side_effect = [
        script_retriever.socket.timeout(),
        script_retriever.socket.timeout(),
        script_retriever.socket.timeout(),
        mock_success,
    ]
    self.assertIsNone(self.retriever._DownloadUrl(url, self.dest_dir))
    self.assertEqual(self.mock_logger.warning.call_count, 1)

  @mock.patch('google_compute_engine.metadata_scripts.script_retriever.time')
  @mock.patch('google_compute_engine.metadata_scripts.script_retriever.tempfile.NamedTemporaryFile')
  @mock.patch('google_compute_engine.metadata_scripts.script_retriever.urlretrieve.urlretrieve')
  def testDownloadUrlWithRetry(self, mock_retrieve, mock_tempfile, mock_time):
    url = 'http://www.google.com/fake/url'
    mock_tempfile.return_value = mock_tempfile
    mock_tempfile.name = self.dest
    mock_success = mock.Mock()
    mock_success.getcode.return_value = script_retriever.httpclient.OK
    # Success after 2 timeout. Since max_retry = 3, the final result is success.
    mock_retrieve.side_effect = [
        script_retriever.socket.timeout(),
        script_retriever.socket.timeout(),
        mock_success,
    ]
    self.assertIsNotNone(self.retriever._DownloadUrl(url, self.dest_dir))

  @mock.patch('google_compute_engine.metadata_scripts.script_retriever.tempfile.NamedTemporaryFile')
  @mock.patch('google_compute_engine.metadata_scripts.script_retriever.urlretrieve.urlretrieve')
  def testDownloadUrlException(self, mock_retrieve, mock_tempfile):
    url = 'http://www.google.com/fake/url'
    mock_tempfile.return_value = mock_tempfile
    mock_tempfile.name = self.dest
    mock_retrieve.side_effect = Exception('Error.')
    self.assertIsNone(self.retriever._DownloadUrl(url, self.dest_dir))
    self.assertEqual(self.mock_logger.warning.call_count, 1)

  def _CreateUrls(self, bucket, obj, gs_match=True):
    """Creates a URL for each of the supported Google Storage URL formats.

    Args:
      bucket: string, the Google Storage bucket name.
      obj: string, the object name in the bucket.
      gs_match: bool, True if the bucket and object names are valid.

    Returns:
      (list, dict):
      list, the URLs to download.
      dict, a Google Storage URL mapped to the expected 'gs://' format.
    """
    gs_url = 'gs://%s/%s' % (bucket, obj)
    gs_urls = {gs_url: gs_url}
    url_formats = [
        'http://%s.storage.googleapis.com/%s',
        'https://%s.storage.googleapis.com/%s',
        'http://storage.googleapis.com/%s/%s',
        'https://storage.googleapis.com/%s/%s',
        'http://commondatastorage.googleapis.com/%s/%s',
        'https://commondatastorage.googleapis.com/%s/%s',
    ]
    url_formats = [url % (bucket, obj) for url in url_formats]
    if gs_match:
      gs_urls.update(dict((url, gs_url) for url in url_formats))
      return ([], gs_urls)
    else:
      return (url_formats, gs_urls)

  def testDownloadScript(self):
    mock_auth_download = mock.Mock()
    self.retriever._DownloadAuthUrl = mock_auth_download
    mock_download = mock.Mock()
    self.retriever._DownloadUrl = mock_download
    download_urls = []
    download_gs_urls = {}

    component_urls = [
        ('@#$%^', '\n\n\n\n', False),
        ('///////', '///////', False),
        ('Abc', 'xyz', False),
        (' abc', 'xyz', False),
        ('abc', 'xyz?', False),
        ('abc', 'xyz*', False),
        ('', 'xyz', False),
        ('a', 'xyz', False),
        ('abc', '', False),
        ('hello', 'world', True),
        ('hello', 'world!', True),
        ('hello', 'world !', True),
        ('hello', 'w o r l d ', True),
        ('hello', 'w\no\nr\nl\nd ', True),
        ('123_hello', '1!@#$%^', True),
        ('123456', 'hello.world', True),
    ]

    for bucket, obj, gs_match in component_urls:
      urls, gs_urls = self._CreateUrls(bucket, obj, gs_match=gs_match)
      download_urls.extend(urls)
      download_gs_urls.update(gs_urls)

    # All Google Storage URLs are downloaded with an authentication token.
    for url, gs_url in download_gs_urls.items():
      mock_download.reset_mock()
      mock_auth_download.reset_mock()
      self.retriever._DownloadScript(gs_url, self.dest_dir)
      new_gs_url = gs_url.replace('gs://', 'https://storage.googleapis.com/')
      mock_auth_download.assert_called_once_with(new_gs_url, self.dest_dir)
      mock_download.assert_not_called()

    for url in download_urls:
      mock_download.reset_mock()
      self.retriever._DownloadScript(url, self.dest_dir)
      mock_download.assert_called_once_with(url, self.dest_dir)

    for url, gs_url in download_gs_urls.items():
      if url.startswith('gs://'):
        continue
      mock_auth_download.reset_mock()
      mock_auth_download.return_value = None
      mock_download.reset_mock()
      self.retriever._DownloadScript(url, self.dest_dir)
      mock_auth_download.assert_called_once_with(url, self.dest_dir)

  @mock.patch('google_compute_engine.metadata_scripts.script_retriever.tempfile.NamedTemporaryFile')
  def testGetAttributeScripts(self, mock_tempfile):
    script = 'echo Hello World.\n'
    script_dest = '/tmp/script'
    script_url = 'gs://fake/url'
    script_url_dest = '/tmp/script_url'
    attribute_data = {
        '%s-script' % self.script_type: '\n%s' % script,
        '%s-script-url' % self.script_type: script_url,
    }
    expected_data = {
        '%s-script' % self.script_type: script_dest,
        '%s-script-url' % self.script_type: script_url_dest,
    }
    # Mock saving a script to a file.
    mock_dest = mock.Mock()
    mock_dest.name = script_dest
    mock_tempfile.__enter__.return_value = mock_dest
    mock_tempfile.return_value = mock_tempfile
    # Mock downloading a script from a URL.
    mock_download = mock.Mock()
    mock_download.return_value = script_url_dest
    self.retriever._DownloadScript = mock_download

    self.assertEqual(
        self.retriever._GetAttributeScripts(attribute_data, self.dest_dir),
        expected_data)
    self.assertEqual(self.mock_logger.info.call_count, 2)
    mock_dest.write.assert_called_once_with(script)
    mock_download.assert_called_once_with(script_url, self.dest_dir)

  def testGetAttributeScriptsNone(self):
    attribute_data = {}
    expected_data = {}
    self.assertEqual(
        self.retriever._GetAttributeScripts(attribute_data, self.dest_dir),
        expected_data)
    self.mock_logger.info.assert_not_called()

  @mock.patch('google_compute_engine.metadata_scripts.script_retriever.tempfile.NamedTemporaryFile')
  def testGetScripts(self, mock_tempfile):
    script_dest = '/tmp/script'
    script_url_dest = '/tmp/script_url'
    metadata = {
        'instance': {
            'attributes': {
                '%s-script' % self.script_type: 'a',
                '%s-script-url' % self.script_type: 'b',
            },
        },
        'project': {
            'attributes': {
                '%s-script' % self.script_type: 'c',
                '%s-script-url' % self.script_type: 'd',
            },
        },
    }
    expected_data = {
        '%s-script' % self.script_type: script_dest,
        '%s-script-url' % self.script_type: script_url_dest,
    }
    self.mock_watcher.GetMetadata.return_value = metadata
    self.retriever.watcher = self.mock_watcher
    # Mock saving a script to a file.
    mock_dest = mock.Mock()
    mock_dest.name = script_dest
    mock_tempfile.__enter__.return_value = mock_dest
    mock_tempfile.return_value = mock_tempfile
    # Mock downloading a script from a URL.
    mock_download = mock.Mock()
    mock_download.return_value = script_url_dest
    self.retriever._DownloadScript = mock_download

    self.assertEqual(self.retriever.GetScripts(self.dest_dir), expected_data)
    self.assertEqual(self.mock_logger.info.call_count, 2)
    self.assertEqual(self.mock_logger.warning.call_count, 0)
    mock_dest.write.assert_called_once_with('a')
    mock_download.assert_called_once_with('b', self.dest_dir)

  def testGetScriptsNone(self):
    metadata = {
        'instance': {
            'attributes': None,
        },
        'project': {
            'attributes': None,
        },
    }
    expected_data = {}
    self.mock_watcher.GetMetadata.return_value = metadata
    self.retriever.watcher = self.mock_watcher
    self.assertEqual(self.retriever.GetScripts(self.dest_dir), expected_data)
    self.mock_logger.info.assert_not_called()

  def testGetScriptsNoMetadata(self):
    metadata = None
    expected_data = {}
    self.mock_watcher.GetMetadata.return_value = metadata
    self.retriever.watcher = self.mock_watcher
    self.assertEqual(self.retriever.GetScripts(self.dest_dir), expected_data)
    self.mock_logger.info.assert_not_called()
    self.assertEqual(self.mock_logger.warning.call_count, 2)

  @mock.patch('google_compute_engine.metadata_scripts.script_retriever.tempfile.NamedTemporaryFile')
  def testGetScriptsFailed(self, mock_tempfile):
    script_dest = '/tmp/script'
    script_url_dest = None
    metadata = {
        'instance': {
            'attributes': {
                '%s-script' % self.script_type: 'a',
                '%s-script-url' % self.script_type: 'b',
            },
        },
        'project': {
            'attributes': {
                '%s-script' % self.script_type: 'c',
                '%s-script-url' % self.script_type: 'd',
            },
        },
    }
    expected_data = {
        '%s-script' % self.script_type: script_dest,
        '%s-script-url' % self.script_type: script_url_dest,
    }
    self.mock_watcher.GetMetadata.return_value = metadata
    self.retriever.watcher = self.mock_watcher
    # Mock saving a script to a file.
    mock_dest = mock.Mock()
    mock_dest.name = script_dest
    mock_tempfile.__enter__.return_value = mock_dest
    mock_tempfile.return_value = mock_tempfile
    # Mock downloading a script from a URL.
    mock_download = mock.Mock()
    mock_download.return_value = None
    self.retriever._DownloadScript = mock_download

    self.assertEqual(self.retriever.GetScripts(self.dest_dir), expected_data)
    self.assertEqual(self.mock_logger.info.call_count, 2)
    self.assertEqual(self.mock_logger.warning.call_count, 1)


if __name__ == '__main__':
  unittest.main()
