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


"""Image manifest."""


import json
from gcimagebundlelib import utils


class ImageManifest(object):
  """Retrieves metadata from the instance and stores it in manifest.json.

  The image manifest is a JSON file that is bundled along side the disk.

  Included Metadata
  - Licenses
  """

  def __init__(self, http=utils.Http(), is_gce_instance=True):
    self._http = http
    self._licenses = []
    self._is_gce_instance = is_gce_instance

  def CreateIfNeeded(self, file_path):
    """Creates the manifest file to the specified path if it's needed.

    Args:
      file_path: Location of where the manifest should be written to.

    Returns:
      True Manifest was written to file_path.
      False Manifest was not created.
    """
    if self._is_gce_instance:
      self._LoadLicenses()
    if self._IsManifestNeeded():
      with open(file_path, 'w') as manifest_file:
        self._WriteToFile(manifest_file)
      return True
    return False

  def _LoadLicenses(self):
    """Loads the licenses from the metadata server if they exist."""
    response = self._http.GetMetadata('instance/', recursive=True)
    instance_metadata = json.loads(response)
    if 'licenses' in instance_metadata:
      for license_obj in instance_metadata['licenses']:
        self._licenses.append(license_obj['id'])

  def _ToJson(self):
    """Formats the image metadata as a JSON object."""
    return json.dumps(
        {
            'licenses': self._licenses
        })

  def _IsManifestNeeded(self):
    """Determines if a manifest should be bundled with the disk."""
    if self._licenses:
      return len(self._licenses)
    return False

  def _WriteToFile(self, file_obj):
    """Writes the manifest data to the file handle."""
    manifest_json = self._ToJson()
    file_obj.write(manifest_json)
