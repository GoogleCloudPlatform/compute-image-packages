#!/usr/bin/python
# Copyright 2017 Google Inc. All Rights Reserved.
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

"""A module for global constants."""

import platform

OSLOGIN_CONTROL_SCRIPT = 'google_oslogin_control'
OSLOGIN_NSS_CACHE = '/etc/passwd.cache'
OSLOGIN_NSS_CACHE_SCRIPT = 'google_oslogin_nss_cache'

if platform.system() == 'FreeBSD':
    LOCALBASE = '/usr/local'
    BOTOCONFDIR = '/usr/local'
    SYSCONFDIR = '/usr/local/etc'
    LOCALSTATEDIR = '/var/spool'
elif platform.system() == 'OpenBSD':
    LOCALBASE = '/usr/local'
    BOTOCONFDIR = ''
    SYSCONFDIR = '/usr/local/etc'
    LOCALSTATEDIR = '/var/spool'
else:
    LOCALBASE = ''
    BOTOCONFDIR = ''
    SYSCONFDIR = '/etc/default'
    LOCALSTATEDIR = '/var'
