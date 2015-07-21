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

from Vyatta import CfgClient
from contextlib import contextmanager

@contextmanager
def VyattaCfgClient():
  client = CfgClient.CfgClient()
  sessid = str(os.getpid())
  
  # save the old IDs 
  old_euid = os.getuid()
  old_egid = os.getegid()
  old_gid = os.getgid()
  
  # get uid of configd and gid of vyattacfg
  configd_uid = pwd.getpwnam("configd").pw_uid
  vyattacfg_gid = pwd.getpwnam("configd").pw_gid
  print "configd: ", configd_uid
  print "vyattacfg: ", vyattacfg_gid

  # set the new configd uid and vyattacfg gid 
  os.setegid(vyattacfg_gid)
  #os.setgid(vyattacfg_gid)
  os.seteuid(configd_uid)
  
  client.SessionSetup(sessid)
  try:
    yield client
  except CfgClient.CfgClientException as e:
    client.Discard()
    raise e
  finally:
    client.SessionTeardown()
    os.seteuid(old_euid)
    os.setegid(old_egid)
    os.setgid(old_gid)
    
      
class VyattaSystem(object):
  def UserAddVyatta(self, username, passwd):
    """Adds the user to the VRouter's Configuration."""

    print "Inside CreateAccount()"
    prefix_path = ["system", "login", "user", username]
    
    with VyattaCfgClient() as client:
      print ("IN: egid:%s  gid:%s  euid:%s  uid:%s"
             % (os.getegid(), os.getgid(), os.geteuid(), os.getuid()))
      
      # add the user if they do not exist
      if not client.NodeExists(client.AUTO, prefix_path):
        try:
          passwd_path = prefix_path + ["authentication",
                                       "plaintext-password", passwd]
          client.Set(passwd_path)
          client.Commit("Google Compute Engine Agent")
          client.Save()
          print "%s added" % username
        except CfgClient.CfgClientException as e:
          print "Unable to set passwd:", e.what()
        
    # outside of context manager
    print ("OUT: egid:%s  gid:%s  euid:%s  uid:%s"
           % (os.getegid(), os.getgid(), os.geteuid(), os.getuid()))

  def MakeUserSudoerVyatta(self, username):
    """Set the specified user to superuser in the config system"""

    with VyattaCfgClient() as client:
      path = ["system", "login", "user", username, "level", "superuser"]
      
      if not client.NodeExists(client.AUTO, path):
        try:
          client.Set(path)
          client.Commit("Google Compute Engine Agent")
          client.Save()
          print "%s made sudoer" % username
        except CfgClient.CfgClientException as e:
          print "Unable to set sudoer:", e.what()
      
  def AuthorizeSshKeysVyatta(self, username, ssh_keys):
    """Sets the specified user's ssh_keys"""
    
    print "Inside SetSshKeys()"
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
        # set the key value and type if they do not exist 
        if not client.NodeExists(client.AUTO, prefix_path):
          try:
            path_value = prefix_path + ["key", key_value]
            path_type = prefix_path + ["type", key_type]
            
            client.Set(path_value)
            client.Set(path_type)
            client.Commit("Google Compute Engine Agent")
            client.Save()
            print "%s ssh key's added" % username
          except Exception as e:
            print "Unable to set ssh_key", e.what()
            #raise e
        key_number += 1
