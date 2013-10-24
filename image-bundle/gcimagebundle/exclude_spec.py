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


"""Exclude file specification."""



import logging
import os


class ExcludeSpec(object):
  """Specifies how exclusion of a path should be handled."""

  def __init__(self, path, preserve_file=False, preserve_dir=False,
               preserve_subdir=False):
    self.path = path
    self.preserve_dir = preserve_dir
    self.preserve_file = False
    self.preserve_subdir = False
    # Preserve files and subdirs only if dir is preserved.
    if preserve_file and preserve_dir:
      self.preserve_file = True
    if preserve_subdir and preserve_dir:
      self.preserve_subdir = True

  def ShouldExclude(self, filename):
    prefix = os.path.commonprefix([filename, self.path])
    if prefix == self.path:
      if ((self.preserve_dir and filename == self.path) or
          (self.preserve_subdir and os.path.isdir(filename)) or
          (self.preserve_file and os.path.isfile(filename))):
        logging.warning('preserving %s', filename)
        return False
      return True
    return False

  def GetSpec(self):
    return '(%s, %d:%d:%d)' % (self.path, self.preserve_file, self.preserve_dir,
                               self.preserve_subdir)

  def GetRsyncSpec(self, src):
    """Returns exclude spec in a format required by rsync.

    Args:
      src: source directory path passed to rsync. rsync expects exclude-spec to
        be relative to src directory.

    Returns:
      A string of exclude filters in rsync exclude-from file format.
    """
    spec = ''
    prefix = os.path.commonprefix([src, self.path])
    if prefix == src:
      relative_path = os.path.join('/', self.path[len(prefix):])
      if self.preserve_dir:
        spec += '+ %s\n' % relative_path
        if self.preserve_file or self.preserve_subdir:
          if os.path.isdir(self.path):
            for f in os.listdir(self.path):
              file_path = os.path.join(self.path, f)
              relative_file_path = os.path.join(relative_path, f)
              if self.preserve_file and os.path.isfile(file_path):
                spec += '+ %s\n' % relative_file_path
              if self.preserve_subdir and os.path.isdir(file_path):
                spec += '+ %s\n' % relative_file_path
      else:
        spec += '- %s\n' % relative_path
      spec += '- %s\n' % os.path.join(relative_path, '**')
    return spec
