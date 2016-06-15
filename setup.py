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

"""Create a Python package of the Linux guest environment."""

import glob
import os
import sys

import setuptools


def GetInitFiles(path):
  """Get the list of relative paths to init files.

  Args:
    path: string, the relative path to the source directory.

  Returns:
    list, the relative path strings for init files.
  """
  valid = '%s/*' % path
  invalid = '%s/*.sh' % path
  return list(set(glob.glob(valid)) - set(glob.glob(invalid)))


# Common data files to add as part of all Linux distributions.
data_files = [
    ('/etc/default', ['package/instance_configs.cfg']),
]


# Data files specific to the various Linux init systems.
data_files_dict = {
    None: [],
    'systemd': [('/usr/lib/systemd/system', GetInitFiles('package/systemd'))],
    'sysvinit': [('/etc/init.d', GetInitFiles('package/sysvinit'))],
    'upstart': [('/etc/init', GetInitFiles('package/upstart'))],
}


if os.environ.get('CONFIG') not in data_files_dict.keys():
  keys = ', '.join([key for key in data_files_dict.keys() if key])
  sys.exit('Expected "CONFIG" environment variable set to one of [%s].' % keys)


setuptools.setup(
    author='Google Compute Engine Team',
    author_email='gc-team@google.com',
    data_files=data_files + data_files_dict.get(os.environ.get('CONFIG')),
    description='Google Compute Engine',
    include_package_data=True,
    install_requires=['boto'],
    license='Apache Software License',
    long_description='Google Compute Engine guest environment.',
    name='google-compute-engine',
    packages=setuptools.find_packages(),
    scripts=glob.glob('scripts/*'),
    url='https://github.com/GoogleCloudPlatform/compute-image-packages',
    version='2.0.0',
    # Entry points create scripts in /usr/bin that call a function.
    entry_points={
        'console_scripts': [
            'google_accounts_daemon=google_compute_engine.accounts.accounts_daemon:main',
            'google_clock_skew_daemon=google_compute_engine.clock_skew.clock_skew_daemon:main',
            'google_ip_forwarding_daemon=google_compute_engine.ip_forwarding.ip_forwarding_daemon:main',
            'google_instance_setup=google_compute_engine.instance_setup.instance_setup:main',
            'google_metadata_script_runner=google_compute_engine.metadata_scripts.script_manager:main',
        ],
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: No Input/Output (Daemon)',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Internet',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Installation/Setup',
        'Topic :: System :: Systems Administration',
    ],
)
