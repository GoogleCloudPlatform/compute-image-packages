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

"""A library for logging text to SysLog and the serial console."""

import logging
import logging.handlers


def Logger(name, debug=False, facility=None):
  """Get a logging object with handlers for sending logs to SysLog.

  Args:
    name: string, the name of the logger which will be added to log entries.
    debug: bool, True if debug output should write to the console.
    facility: int, an encoding of the SysLog handler's facility and priority.

  Returns:
    logging object, an object for logging entries.
  """
  logger = logging.getLogger(name)
  logger.handlers = []
  logger.propagate = False
  logger.setLevel(logging.DEBUG)
  formatter = logging.Formatter(name + ': %(levelname)s %(message)s')

  if debug:
    # Create a handler for console logging.
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

  if facility:
    # Create a handler for sending logs to SysLog.
    syslog_handler = logging.handlers.SysLogHandler(
        address='/dev/log', facility=facility)
    syslog_handler.setLevel(logging.INFO)
    syslog_handler.setFormatter(formatter)
    logger.addHandler(syslog_handler)

  return logger
