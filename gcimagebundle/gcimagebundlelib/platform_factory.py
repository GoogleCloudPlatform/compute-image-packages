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


"""Factory that guesses the correct platform and creates it."""

import logging

from gcimagebundlelib import centos
from gcimagebundlelib import fedora
from gcimagebundlelib import debian
from gcimagebundlelib import gcel
from gcimagebundlelib import opensuse
from gcimagebundlelib import rhel
from gcimagebundlelib import sle
from gcimagebundlelib import ubuntu


class UnknownPlatformException(Exception):
  """The platform could not be correctly determined."""


class PlatformFactory(object):
  """Guess the platform and create it."""

  def __init__(self, root='/'):
    self.__root = root
    self.__registry = {}
    self.__platform_registry = {}
    self.Register('Centos', centos.Centos)
    self.Register('Fedora', fedora.Fedora)
    self.Register('Debian', debian.Debian)
    self.Register('GCEL', gcel.Gcel)
    self.Register('openSUSE', opensuse.OpenSUSE)
    self.Register('Red Hat Enterprise Linux', rhel.RHEL)
    self.Register('SUSE Linux Enterprise', sle.SLE)
    self.Register('Ubuntu', ubuntu.Ubuntu)

  def Register(self, name, klass):
    self.__registry[name] = klass

  def GetPlatform(self):
    for name in self.__registry:
      if self.__registry[name].IsThisPlatform(self.__root):
        logging.info('found platform %s', name)
        return self.__registry[name]()
      else:
        logging.debug('skipping platform %s %s ', name, self.__registry[name])
    raise UnknownPlatformException('Could not determine host platform.')
