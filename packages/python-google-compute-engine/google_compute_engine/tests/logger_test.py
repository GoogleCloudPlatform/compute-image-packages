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

"""Unittest for logger.py module."""

from google_compute_engine import logger
from google_compute_engine.test_compat import mock
from google_compute_engine.test_compat import unittest


class LoggerTest(unittest.TestCase):

  @mock.patch('google_compute_engine.logger.logging.handlers.SysLogHandler')
  @mock.patch('google_compute_engine.logger.logging.StreamHandler')
  @mock.patch('google_compute_engine.logger.logging.NullHandler')
  def testLogger(self, mock_null, mock_stream, mock_syslog):
    mock_null.return_value = mock_null
    mock_stream.return_value = mock_stream
    mock_syslog.return_value = mock_syslog
    name = 'test'

    # Verify basic logger setup.
    named_logger = logger.Logger(name=name, debug=True)
    mock_stream.setLevel.assert_called_once_with(logger.logging.DEBUG)
    self.assertEqual(named_logger.handlers, [mock_null, mock_stream])

    # Verify logger setup with a facility.
    address = '/dev/log'
    facility = 1
    named_logger = logger.Logger(name=name, debug=True, facility=facility)
    mock_syslog.assert_called_once_with(address=address, facility=facility)
    mock_syslog.setLevel.assert_called_once_with(logger.logging.INFO)
    self.assertEqual(
        named_logger.handlers, [mock_null, mock_stream, mock_syslog])

    # Verify the handlers are reset during repeated calls.
    named_logger = logger.Logger(name=name, debug=False)
    self.assertEqual(named_logger.handlers, [mock_null])


if __name__ == '__main__':
  unittest.main()
