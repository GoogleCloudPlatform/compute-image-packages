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
import subprocess
import sys

if sys.version_info >= (3, 6):
  import distro
else:
  import platform as distro

distribution = distro.linux_distribution()
distro_name = distribution[0].lower()
distro_version = distribution[1].split('.')[0]
distro_utils = None

if 'centos' in distro_name and distro_version == '6':
  import google_compute_engine.distro.el_6.utils as distro_utils
elif 'centos' in distro_name:
  import google_compute_engine.distro.el_7.utils as distro_utils
elif 'red hat enterprise linux' in distro_name and distro_version == '6':
  import google_compute_engine.distro.el_6.utils as distro_utils
elif 'red hat enterprise linux' in distro_name:
  import google_compute_engine.distro.el_7.utils as distro_utils
elif 'debian' in distro_name and distro_version == '8':
  import google_compute_engine.distro.debian_8.utils as distro_utils
elif 'debian' in distro_name:
  import google_compute_engine.distro.debian_9.utils as distro_utils
elif 'suse' in distro_name and distro_version == '11':
  import google_compute_engine.distro.sles_11.utils as distro_utils
elif 'suse' in distro_name:
  import google_compute_engine.distro.sles_12.utils as distro_utils
else:
  # Default to Debian 9.
  import google_compute_engine.distro.debian_9.utils as distro_utils

RETRY_LIMIT = 3
TIMEOUT = 10

if sys.version_info >= (3, 0):
  # Python 3 imports.
  import configparser as parser
  import http.client as httpclient
  import io as stringio
  import urllib.error as urlerror
  import urllib.parse as urlparse
  import urllib.request as urlrequest
  import urllib.request as urlretrieve
else:
  # Python 2 imports.
  import ConfigParser as parser
  import httplib as httpclient
  import StringIO as stringio
  import urllib as urlparse
  import urllib as urlretrieve
  import urllib2 as urlrequest
  import urllib2 as urlerror

if sys.version_info < (2, 7):

  class NullHandler(logging.Handler):

    def emit(self, record):
      pass

    def handle(self, record):
      pass

    def createLock(self):
      pass

  logging.NullHandler = NullHandler

if sys.version_info < (2, 7, 9):

  # Native Python libraries do not check SSL certificates.
  def curlretrieve(url, filename=None, *args, **kwargs):
    command = ['curl', '--max-time', str(TIMEOUT), '--retry', str(RETRY_LIMIT)]
    if filename:
      command += ['-o', filename]
    command += ['--', url]
    subprocess.check_call(command)

  urlretrieve.urlretrieve = curlretrieve
