#!/usr/bin/python
# Copyright 2015 Brocade Inc. All Rights Reserved.
#
# Author: Brandon Luu bluu@brocade.com
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

import os
import sys
import pwd
import grp
import traceback
import logging

from vyatta import configd
from contextlib import contextmanager

@contextmanager
def VyattaCfgClient():
  client = configd.Client()
  sessid = str(os.getpid())

  # save the old IDs
  old_euid = os.getuid()
  old_egid = os.getegid()
  old_gid = os.getgid()

  # get uid of configd and gid of vyattacfg
  configd_uid = pwd.getpwnam("configd").pw_uid
  vyattacfg_gid = grp.getgrnam("vyattacfg").gr_gid

  # set the new configd uid and vyattacfg gid
  os.setegid(vyattacfg_gid)
  os.seteuid(configd_uid)

  client.session_setup(sessid)
  try:
    yield client
  except configd.Exception as e:
    client.discard()
    raise e
  finally:
    client.session_teardown()
    os.seteuid(old_euid)
    os.setegid(old_egid)
    os.setgid(old_gid)


class VyattaSystem(object):
  def UserAddVyatta(self, username, passwd):
    """Adds the user to the VRouter's Configuration."""

    prefix_path = ["system", "login", "user", username]

    with VyattaCfgClient() as client:
      # add the user if they do not exist
      if not client.node_exists(client.AUTO, prefix_path):
        try:
          passwd_path = prefix_path + ["authentication",
                                       "plaintext-password", passwd]
          client.set(passwd_path)
          client.commit("Google Compute Engine Agent")
          client.save()
          logging.info(username + " added")
        except configd.Exception as e:
          logging.error("Unable to set passwd: %s", e.what())

  def MakeUserSudoerVyatta(self, username):
    """Set the specified user to superuser in the config system"""

    with VyattaCfgClient() as client:
      path = ["system", "login", "user", username, "level", "superuser"]

      if not client.node_exists(client.AUTO, path):
        try:
          client.set(path)
          client.commit("Google Compute Engine Agent")
          client.save()
          logging.info(username + " made sudoer")
        except configd.Exception as e:
          logging.error("Unable to set sudoer: %s", e.what())

  def AuthorizeSshKeysVyatta(self, username, ssh_keys):
    """Sets the specified user's ssh_keys"""
    key_number = 0

    with VyattaCfgClient() as client:
      for ssh_key in ssh_keys:
        # extract the values from the ssh_key block
        key_split = ssh_key.split()
        key_type = key_split[0]
        key_value = key_split[1]
        key_user = key_split[2]

        prefix_path = ["system", "login", "user", username, "authentication",
                       "public-keys", key_user + "_key" + str(key_number)]

        path_value = prefix_path + ["key", key_value]
        path_type = prefix_path + ["type", key_type]

        # set the key value and type if the key does not exist
        if not client.node_exists(client.AUTO, path_value):
          try:
            client.set(path_value)
            client.set(path_type)
            client.commit("Google Compute Engine Agent")
            client.save()
            logging.info(username + " ssh key added")
          except configd.Exception as e:
            logging.error("Unable to set ssh_key: %s", e.what())
        key_number += 1
