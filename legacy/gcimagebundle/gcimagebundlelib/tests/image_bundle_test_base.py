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


"""Base class for image_bundle unittests."""


__pychecker__ = 'no-local'  # for unittest


import os
import re
import shutil
import subprocess
import tarfile
import tempfile
import unittest
import urllib2

from gcimagebundlelib import manifest
from gcimagebundlelib.os_platform import Platform
from gcimagebundlelib import utils


class InvalidOverwriteFileException(Exception):
  """Invalid overwrite target was passed to MockPlatform.Overwrite method."""


class MockPlatform(Platform):
  """Mock platform for image bundle unit tests."""
  OVERWRITE_LIST = ['test1']

  def __init__(self, tmp_root):
    super(MockPlatform, self).__init__()
    self.tmp_root = tmp_root

  def Overwrite(self, filename, arcname, tmpdir):
    temp = tempfile.mktemp(dir=tmpdir)
    if arcname != 'test1':
      raise InvalidOverwriteFileException(arcname)
    fd = open(temp, 'w')
    fd.write(open(filename).read())
    fd.write('something extra.')
    fd.close()
    return temp


class MockHttp(utils.Http):
  """Fake implementation of the utils.Http client. Used for metadata queries."""
  def __init__(self):
    self._instance_response = '{"hostname":"test"}'

  def Get(self, request, timeout=None):
    """Accepts an Http request and returns a precanned response."""
    url = request.get_full_url()
    if url == utils.METADATA_URL_PREFIX:
      return 'v1/'
    elif url.startswith(utils.METADATA_V1_URL_PREFIX):
      url = url.replace(utils.METADATA_V1_URL_PREFIX, '')
      if url == 'instance/?recursive=true':
        return self._instance_response
    raise urllib2.HTTPError

class StatvfsResult:
  """ A struct for partial os.statvfs result, used to mock the result. """

  def __init__(self, f_bsize, f_blocks, f_bfree):
    self.f_bsize = f_bsize
    self.f_blocks = f_blocks
    self.f_bfree = f_bfree

class ImageBundleTest(unittest.TestCase):
  """ImageBundle Unit Test Base Class."""

  def setUp(self):
    self.tmp_root = tempfile.mkdtemp(dir='/tmp')
    self.tmp_path = tempfile.mkdtemp(dir=self.tmp_root)
    self._http = MockHttp()
    self._manifest = manifest.ImageManifest(http=self._http, is_gce_instance=True)
    self._SetupFilesystemToTar()

  def tearDown(self):
    self._CleanupFiles()

  def _SetupFilesystemToTar(self):
    """Creates some directory structure to tar."""
    if os.path.exists(self.tmp_path):
      shutil.rmtree(self.tmp_path)
    os.makedirs(self.tmp_path)
    with open(self.tmp_path + '/test1', 'w') as fd:
      print >> fd, 'some text'
    shutil.copyfile(self.tmp_path + '/test1', self.tmp_path + '/test2')
    os.makedirs(self.tmp_path + '/dir1')
    os.makedirs(self.tmp_path + '/dir1/dir11')
    os.makedirs(self.tmp_path + '/dir2')
    os.makedirs(self.tmp_path + '/dir2/dir1')
    os.symlink(self.tmp_path + '/test1', self.tmp_path + '/dir1/sl1')
    os.link(self.tmp_path + '/test2', self.tmp_path + '/dir1/hl2')
    os.symlink(self.tmp_path + '/test2', self.tmp_path + '/dir2/sl2')
    os.link(self.tmp_path + '/test1', self.tmp_path + '/dir2/hl1')

  def _CleanupFiles(self):
    """Removes the files under test directory."""
    if os.path.exists(self.tmp_root):
      shutil.rmtree(self.tmp_root)

  def _VerifyTarHas(self, tar, expected):
    p = subprocess.Popen(['tar -tf %s' % tar],
                         stdout=subprocess.PIPE, shell=True)
    found = p.communicate()[0].split('\n')
    if './' in found:
      found.remove('./')
    if '' in found:
      found.remove('')
    self._AssertListEqual(expected, found)

  def _VerifyFileInTarEndsWith(self, tar, filename, text):
    tf = tarfile.open(tar, 'r:gz')
    fd = tf.extractfile(filename)
    file_content = fd.read()
    self.assertTrue(file_content.endswith(text))

  def _AssertListEqual(self, list1, list2):
    """Asserts that, when sorted, list1 and list2 are identical."""
    sorted_list1 = [re.sub(r'/$', '', x) for x in list1]
    sorted_list2 = [re.sub(r'/$', '', x) for x in list2]
    sorted_list1.sort()
    sorted_list2.sort()
    self.assertEqual(sorted_list1, sorted_list2)
