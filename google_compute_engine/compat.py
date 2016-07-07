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

"""A module for resolving compatibility issues between Python 2 and Python 3."""

import logging
import sys

if sys.version_info >= (3,):
  # Python 3 imports.
  import configparser as parser
  import http.client as httpclient
  import urllib.error as urlerror
  import urllib.parse as urlparse
  import urllib.request as urlrequest
  import urllib.request as urlretrieve
else:
  # Python 2 imports.
  import ConfigParser as parser
  import httplib as httpclient
  import urllib as urlparse
  import urllib as urlretrieve
  import urllib2 as urlrequest
  import urllib2 as urlerror

if sys.version_info < (2,7,):
  class NullHandler(logging.Handler):
    def emit(self, record):
      pass

    def handle(self, record):
      pass

    def createLock(self):
      pass

  logging.NullHandler = NullHandler
