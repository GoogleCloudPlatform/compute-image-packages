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

"""Manage extra network interface addresses on a GCE instance.

Fetch a list of public endpoint IPs from the metadata server, compare it with
what's configured on eth0, and add/remove addresses from eth0 to make them
match.  Only remove those which match our proto code.

This must be run by root. If it reads any malformed data, it will take no
action.

Command used to add ips:
  ip route add to local $IP/32 dev eth0 proto 66
Command used to fetch list of configured IPs:
  ip route ls table local type local dev eth0 scope host proto 66
"""


import logging
import os
import re
import socket
import time
import urllib2

PUBLIC_ENDPOINT_URL_PREFIX = (
'http://169.254.169.254/computeMetadata/v1/instance/network-interfaces/0/forwarded-ips/?recursive=true&alt=text&wait_for_change=true&timeout_sec=60&last_etag=')
GOOGLE_PROTO_ID = 66  # "GG"

class InputError(Exception):
  pass

class AddressManager(object):
  """Manage public endpoint IPs."""

  def __init__(self, system_module, urllib2_module=urllib2, time_module=time):
    self.system = system_module
    self.urllib2 = urllib2_module
    self.time = time_module
    self.ip_path = '/sbin/ip'
    if not os.path.exists(self.ip_path):
        self.ip_path = '/bin/ip'

    # etag header value is hex, so this is guaranteed to not match.
    self.default_last_etag = 'NONE'
    self.ResetEtag()

  def SyncAddressesForever(self):
    while True:
      try:
        # Block until the metadata changes or there is a timeout or error.
        self.SyncAddresses()
      except socket.timeout as e:
        self.ResetEtag()
        logging.warning('Backend timeout.  Retrying.')
      except Exception as e:
        self.ResetEtag()
        logging.error('SyncAddresses exception: %s', e)
      # Don't spin
      self.time.sleep(5)

  def SyncAddresses(self):
    """Main entry point -- syncs configured w/ desired IP addresses."""

    addrs_wanted = self.ReadPublicEndpoints()
    addrs_configured = self.ReadLocalConfiguredAddrs()
    (to_add, to_remove) = self.DiffAddrs(addrs_wanted, addrs_configured)
    self.LogChanges(addrs_wanted, addrs_configured, to_add, to_remove)
    self.AddAddresses(to_add)
    self.DeleteAddresses(to_remove)

  def ResetEtag(self):
    """Reset the etag so the next call will return the current data."""
    self.last_etag = self.default_last_etag

  def ReadPublicEndpoints(self):
    """Fetch list of public endpoint IPs from metadata server."""
    try:
      # If the connection gets abandoned, ensure we don't hang more than
      # 70 seconds.
      url = PUBLIC_ENDPOINT_URL_PREFIX + self.last_etag
      request = urllib2.Request(url)
      request.add_unredirected_header('Metadata-Flavor', 'Google')
      u = self.urllib2.urlopen(request, timeout=70)
      addrs_data = u.read()
      headers = u.info().dict
      self.last_etag = headers.get('etag', self.default_last_etag)
    except urllib2.HTTPError as h:
      self.ResetEtag()
      # 404 is treated like an empty list, for backward compatibility.
      if h.code == 404:
        return []
      raise h
    return self.ParseIPAddrs(addrs_data)

  def ReadLocalConfiguredAddrs(self):
    """Fetch list of addresses we've configured on eth0 already."""
    cmd = ('{0} route ls table local type local dev eth0 scope host ' +
           'proto {1:d}').format(self.ip_path, GOOGLE_PROTO_ID)
    result = self.system.RunCommand(cmd.split())
    if self.IPCommandFailed(result, cmd):
      raise InputError('Can''t check local addresses')
    (rc, stdout, stderr) = result
    return self.ParseIPAddrs(stdout)

  def DiffAddrs(self, addrs_wanted, addrs_configured):
    """"Returns set differences: (to_add, to_remove)."""
    want = set(addrs_wanted)
    have = set(addrs_configured)
    to_add = want - have
    to_remove = have - want
    return (sorted(to_add), sorted(to_remove))

  def LogChanges(self, addrs_wanted, addrs_configured, to_add, to_remove):
    """Log what addrs we are going to change."""
    if not to_add and not to_remove:
      return
    logging.info(
        'Changing public IPs from %s to %s by adding %s and removing %s' % (
            addrs_configured or None,
            addrs_wanted or None,
            to_add or None,
            to_remove or None))

  def AddAddresses(self, to_add):
    """Configure new addresses on eth0."""
    for addr in to_add:
       self.AddOneAddress(addr)

  def AddOneAddress(self, addr):
    """Configure one address on eth0."""
    cmd = '%s route add to local %s/32 dev eth0 proto %d' % (
        self.ip_path, addr, GOOGLE_PROTO_ID)
    result = self.system.RunCommand(cmd.split())
    self.IPCommandFailed(result, cmd)  # Ignore return code

  def DeleteAddresses(self, to_remove):
    """Un-configure a list of addresses from eth0."""
    for addr in to_remove:
      self.DeleteOneAddress(addr)

  def DeleteOneAddress(self, addr):
    """Delete one address from eth0."""
    # This will fail if it doesn't match exactly the specs listed.
    # That'll help ensure we don't remove one added by someone else.
    cmd = '%s route delete to local %s/32 dev eth0 proto %d' % (
        self.ip_path, addr, GOOGLE_PROTO_ID)
    result = self.system.RunCommand(cmd.split())
    self.IPCommandFailed(result, cmd)  # Ignore return code

  # Helper methods
  def ParseIPAddrs(self, addrs_data):
    """Parse and validate IP addrs, return list of strings or None."""
    addrs = addrs_data.strip().split()
    reg = re.compile(r'^([0-9]+.){3}[0-9]+$')
    for addr in addrs:
      if not reg.search(addr):
        raise InputError('Failed to parse ip addr: "%s"' % addr)
    return addrs

  def IPCommandFailed(self, result, cmd):
    """If an /sbin/ip command failed, log and return True."""
    if self.system.RunCommandFailed(
        result, 'Non-zero exit status from: "%s"' % cmd):
      return True
    else:
      return False
