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

"""Authentication module for using Google Compute service accounts."""

import json
import urllib2

from boto.auth_handler import AuthHandler
from boto.auth_handler import NotReadyToAuthenticate

META_DATA_SERVER_BASE_URL=(
    'http://169.254.169.254/computeMetadata/v1')

SERVICE_ACCOUNT_SCOPES_URL=(META_DATA_SERVER_BASE_URL +
    '/instance/service-accounts/%s/scopes?alt=json')
SERVICE_ACCOUNT_TOKEN_URL=(META_DATA_SERVER_BASE_URL +
    '/instance/service-accounts/%s/token?alt=json')

GS_SCOPES = set([
    'https://www.googleapis.com/auth/devstorage.read_only',
    'https://www.googleapis.com/auth/devstorage.read_write',
    'https://www.googleapis.com/auth/devstorage.full_control',
    ])


class ComputeAuth(AuthHandler):
  """Google Compute service account auth handler.

  What happens is that the boto library reads the system config file
  (/etc/boto.cfg) and looks at a config value called 'plugin_directory'.  It
  then loads the python files in that and find classes derived from
  boto.auth_handler.AuthHandler.
  """

  capability = ['google-oauth2', 's3']

  def __init__(self, path, config, provider):
    self.service_account = config.get('GoogleCompute', 'service_account', '')
    if provider.name == 'google' and self.service_account:
      self.scopes = self.__GetGSScopes()
      if not self.scopes:
        raise NotReadyToAuthenticate()
    else:
      raise NotReadyToAuthenticate()

  def __GetJSONMetadataValue(self, url):
    try:
      request = urllib2.Request(url)
      request.add_unredirected_header('Metadata-Flavor', 'Google')
      data = urllib2.urlopen(request).read()
      return json.loads(data)
    except (urllib2.URLError, urllib2.HTTPError, IOError):
      return None

  def __GetGSScopes(self):
    """Return all Google Storage scopes available on this VM."""
    scopes = self.__GetJSONMetadataValue(
        SERVICE_ACCOUNT_SCOPES_URL % self.service_account)
    if scopes:
      return list(GS_SCOPES.intersection(set(scopes)))
    return None

  def __GetAccessToken(self):
    """Return an oauth2 access token for Google Storage."""
    token_info = self.__GetJSONMetadataValue(
        SERVICE_ACCOUNT_TOKEN_URL % self.service_account)
    if token_info:
      return token_info['access_token']
    return None

  def add_auth(self, http_request):
    http_request.headers['Authorization'] = (
        'OAuth %s' % self.__GetAccessToken())
