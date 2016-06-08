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

import sys

from google_compute_engine.compat import httpclient
from google_compute_engine.compat import parser
from google_compute_engine.compat import urlerror
from google_compute_engine.compat import urlparse
from google_compute_engine.compat import urlrequest
from google_compute_engine.compat import urlretrieve

# Import the mock module in Python 3.2.
if sys.version_info >= (3, 3):
  import unittest.mock as mock
else:
  import mock

# Import the unittest2 module to backport testing features to Python 2.6.
if sys.version_info >= (2, 7):
  import unittest
else:
  import unittest2 as unittest

builtin = 'builtins' if sys.version_info >= (3,) else '__builtin__'
