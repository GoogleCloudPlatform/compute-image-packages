# -*- coding: utf-8 -*-
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


"""Tool to bundle root filesystem to a tarball.

Creates a tar bundle and a Manifest, which can be uploaded to image store.
"""



import logging
from optparse import OptionParser
import os
import shutil
import subprocess
import tempfile

from gcimagebundlelib import block_disk
from gcimagebundlelib import exclude_spec
from gcimagebundlelib import platform_factory
from gcimagebundlelib import utils

def SetupArgsParser():
  """Sets up the command line flags."""
  parser = OptionParser()
  parser.add_option('-d', '--disk', dest='disk',
                    default='/dev/sda',
                    help='Disk to bundle.')
  parser.add_option('-r', '--root', dest='root_directory',
                    default='/', metavar='ROOT',
                    help='Root of the file system to bundle.'
                    ' Recursively bundles all sub directories.')
  parser.add_option('-e', '--excludes', dest='excludes',
                    help='Comma separated list of sub directories to exclude.'
                    ' The defaults are platform specific.')
  parser.add_option('-o', '--output_directory', dest='output_directory',
                    default='/tmp/', metavar='DIR',
                    help='Output directory for image.')
  parser.add_option('--output_file_name', dest='output_file_name',
                    default=None, metavar='FILENAME',
                    help=('Output filename for the image. Default is a digest'
                          ' of the image bytes.'))
  parser.add_option('--include_mounts', dest='include_mounts',
                    help='Don\'t ignore mounted filesystems under ROOT.',
                    action='store_true', default=False)
  parser.add_option('-v', '--version',
                    action='store_true', dest='display_version', default=False,
                    help='Print the tool version.')
  parser.add_option('--loglevel', dest='log_level',
                    help='Debug logging level.', default='INFO',
                    choices=['DEBUG', 'INFO', 'WARNING', 'ERROR' 'CRITICAL'])
  parser.add_option('--log_file', dest='log_file',
                    help='Output file for log messages.')
  parser.add_option('-k', '--key', dest='key', default='nebula',
                    help='Public key used for signing the image.')
  parser.add_option('--nocleanup', dest='cleanup',
                    action='store_false', default=True,
                    help=' Do not clean up temporary and log files.')
  #TODO(user): Get dehumanize.
  parser.add_option('--fssize', dest='fs_size', default=10*1024*1024*1024,
                    type='int', help='File system size in bytes')
  parser.add_option('-b', '--bucket', dest='bucket',
                    help='Destination storage bucket')
  parser.add_option('-f', '--filesystem', dest='file_system',
                    default=None,
                    help='File system type for the image.')
  return parser


def VerifyArgs(parser, options):
  """Verifies that commandline flags are consistent."""
  absolute_output_directory = utils.ExpandPath(options.output_directory)
  if not absolute_output_directory:
    parser.error('output bundle directory must be specified.')
  if not os.path.exists(absolute_output_directory):
    parser.error('output bundle directory does not exist.')
  source_disk_fs = utils.GetFilesystemTable(fs_path_filter=options.disk)
  if not source_disk_fs:
    parser.error(('Source disk %s does not exist,'
                  'check via "df -T" command.' % options.disk))
  # Assume the first entry is the best one.
  source_disk_fs = source_disk_fs[0]
  dest_fs = utils.GetFilesystemForFile(absolute_output_directory)
  if not dest_fs:
    parser.error(('Output directory has no associated filesystem,'
                  'check via "df -T" command.' % options.disk))
  # Require another 128 MB extra.
  required_kb = int(source_disk_fs['used']) + 1024 * 128
  if options.fs_size <= required_kb:
    parser.error(('Size of disk image is too small. Increase --fssize.'
                  '--fssize=%s , %s required.' % (options.fs_size, required_kb)))
  if dest_fs['available'] <= required_kb:
    parser.error(('output directory does not have enough space,'
                  '%s available, %s required.' % (dest_fs['available'], required_kb)))
  try:
    utils.Http().GetMetadata('instance/')
  except BaseException:
    parser.error(('Cannot access metadata server.'
                  ' Are you running within a Google Compute Engine instance?'
                  ' Check your /etc/hosts file for an entry for metadata/'
                  ' See https://developers.google.com/compute/docs/building-image for more details.'))

def EnsureSuperUser():
  """Ensures that current user has super user privileges."""
  if os.getuid() != 0:
    logging.warning('Tool must be run as root.')
    exit(-1)


def GetLogLevel(options):
  """Log Level string to logging.LogLevel mapping."""
  level = {
      'DEBUG': logging.DEBUG,
      'INFO': logging.INFO,
      'WARNING': logging.WARNING,
      'ERROR': logging.ERROR,
      'CRITICAL': logging.CRITICAL
  }
  if options.log_level in level:
    return level[options.log_level]
  print 'Invalid logging level. defaulting to INFO.'
  return logging.INFO


def SetupLogging(options, log_dir='/tmp'):
  """Set up logging.

  All messages above INFO level are also logged to console.

  Args:
    options: collection of command line options.
    log_dir: directory used to generate log files.
  """
  if options.log_file:
    logfile = options.log_file
  else:
    logfile = tempfile.mktemp(dir=log_dir, prefix='bundle_log_')
  print 'Starting logging in %s' % logfile
  logging.basicConfig(filename=logfile, level=GetLogLevel(options))
  console = logging.StreamHandler()
  console.setLevel(GetLogLevel(options))
  logging.getLogger().addHandler(console)


def PrintVersionInfo():
  #TODO: Should read from the VERSION file instead.
  logging.info('version 1.1.0')


def GetTargetFilesystem(options):
  if options.file_system:
    return options.file_system
  else:
    fs_table = utils.GetFilesystemTable(fs_path_filter=options.disk)
    return fs_table[0]['type']


def main():
  parser = SetupArgsParser()
  (options, _) = parser.parse_args()
  if options.display_version:
    PrintVersionInfo()
    return 0
  EnsureSuperUser()
  VerifyArgs(parser, options)

  scratch_dir = tempfile.mkdtemp(dir=options.output_directory)
  SetupLogging(options, scratch_dir)
  try:
    guest_platform = platform_factory.PlatformFactory(
        options.root_directory).GetPlatform()
  except platform_factory.UnknownPlatformException:
    logging.critical('Platform is not supported.'
                     ' Platform rules can be added to platform_factory.py.')
    return -1

  temp_file_name = tempfile.mktemp(dir=scratch_dir, suffix='.tar.gz')

  file_system = GetTargetFilesystem(options)
  logging.info('file system = %s', file_system)
  logging.info('disk size = %s bytes', options.fs_size)
  bundle = block_disk.RootFsRaw(options.fs_size, file_system)
  bundle.SetTarfile(temp_file_name)
  if options.disk:
    readlink_command = ['readlink', '-f', options.disk]
    final_path = utils.RunCommand(readlink_command).strip()
    logging.info('Resolved %s to %s', options.disk, final_path)
    bundle.AddDisk(final_path)
    # TODO(user): Find the location where the first partition of the disk
    # is mounted and add it as the source instead of relying on the source
    # param flag
  bundle.AddSource(options.root_directory)
  bundle.SetKey(options.key)
  bundle.SetScratchDirectory(scratch_dir)

  # Merge platform specific exclude list, mounts points
  # and user specified excludes
  excludes = guest_platform.GetExcludeList()
  if options.excludes:
    excludes.extend([exclude_spec.ExcludeSpec(x) for x in
                     options.excludes.split(',')])
  logging.info('exclude list: %s', ' '.join([x.GetSpec() for x in excludes]))
  bundle.AppendExcludes(excludes)
  if not options.include_mounts:
    mount_points = utils.GetMounts(options.root_directory)
    logging.info('ignoring mounts %s', ' '.join(mount_points))
    bundle.AppendExcludes([exclude_spec.ExcludeSpec(x, preserve_dir=True) for x
                           in utils.GetMounts(options.root_directory)])
  bundle.SetPlatform(guest_platform)

  # Verify that bundle attributes are correct and create tar bundle.
  bundle.Verify()
  (fs_size, digest) = bundle.Bundleup()
  if not digest:
    logging.critical('Could not get digest for the bundle.'
                     ' The bundle may not be created correctly')
    return -1
  if fs_size > options.fs_size:
    logging.critical('Size of tar %d exceeds the file system size %d.', fs_size,
                     options.fs_size)
    return -1

  if options.output_file_name:
    output_file = os.path.join(
        options.output_directory, options.output_file_name)
  else:
    output_file = os.path.join(
        options.output_directory, '%s.image.tar.gz' % digest)

  os.rename(temp_file_name, output_file)
  logging.info('Created tar.gz file at %s' % output_file)

  if options.bucket:
    bucket = options.bucket
    if bucket.startswith('gs://'):
      output_bucket = '%s/%s' % (
          bucket, os.path.basename(output_file))
    else:
      output_bucket = 'gs://%s/%s' % (
          bucket, os.path.basename(output_file))
    # TODO: Consider using boto library directly.
    cmd = ['gsutil', 'cp', output_file, output_bucket]
    retcode = subprocess.call(cmd)
    if retcode != 0:
      logging.critical('Failed to copy image to bucket. '
                       'gsutil returned %d. To retry, run the command: %s',
                       retcode, ' '.join(cmd))

      return -1
    logging.info('Uploaded image to %s', output_bucket)

    # If we've uploaded, then we can remove the local file.
    os.remove(output_file)

  if options.cleanup:
    shutil.rmtree(scratch_dir)
