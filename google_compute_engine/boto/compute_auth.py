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

"""Authentication module for using Google Compute service accounts."""

from boto import auth_handler
from google_compute_engine import logger
from google_compute_engine import metadata_watcher

GS_SCOPES = set([
    'https://www.googleapis.com/auth/devstorage.read_only',
    'https://www.googleapis.com/auth/devstorage.read_write',
    'https://www.googleapis.com/auth/devstorage.full_control',
])


class ComputeAuth(auth_handler.AuthHandler):
  """Google Compute service account auth handler.

  The boto library reads the system config file (/etc/boto.cfg) and looks
  at a config value called 'plugin_directory'. It then loads the Python
  files and find classes derived from boto.auth_handler.AuthHandler.
  """

  capability = ['google-oauth2', 's3']

  def __init__(self, path, config, provider):
    self.logger = logger.Logger(name='compute-auth')
    self.watcher = metadata_watcher.MetadataWatcher(logger=self.logger)
    self.service_account = config.get('GoogleCompute', 'service_account', '')
    self.scopes = None
    if provider.name == 'google' and self.service_account:
      self.scopes = self._GetGsScopes()
    if not self.scopes:
      raise auth_handler.NotReadyToAuthenticate()

  def _GetGsScopes(self):
    """Return all Google Storage scopes available on this VM."""
    scopes_key = 'instance/service-accounts/%s/scopes' % self.service_account
    scopes = self.watcher.GetMetadata(metadata_key=scopes_key, recursive=False)
    return list(GS_SCOPES.intersection(set(scopes))) if scopes else None

  def _GetAccessToken(self):
    """Return an oauth2 access token for Google Storage."""
    token_key = 'instance/service-accounts/%s/token' % self.service_account
    token = self.watcher.GetMetadata(metadata_key=token_key, recursive=False)
    return token['access_token'] if token else None

  def add_auth(self, http_request):
    http_request.headers['Authorization'] = 'OAuth %s' % self._GetAccessToken()
