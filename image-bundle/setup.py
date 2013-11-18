#!/usr/bin/env python
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

"""Setup installation module for Image Bundle."""

import os
import distribute_setup
distribute_setup.use_setuptools()

from setuptools import find_packages
from setuptools import setup

CURDIR = os.path.abspath(os.path.dirname(__file__))

def Read(file_name):
  with open(os.path.join(CURDIR, file_name), 'r') as f:
    return f.read().strip()

setup(
    name='gcimagebundle',
    version=Read('VERSION'),
    url='https://github.com/GoogleCloudPlatform/compute-image-packages/tree/master/image-bundle',
    download_url='https://github.com/GoogleCloudPlatform/compute-image-packages/releases',
    license='Apache 2.0',
    author='Google Inc.',
    author_email='gc-team@google.com',
    description=('Image bundling tool for root file system.'),
    long_description=Read('README.md'),
    zip_safe=False,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Topic :: System :: Filesystems',
        'Topic :: Utilities',
    ],
    platforms='any',
    include_package_data=True,
    packages=find_packages(exclude=['distribute_setup']),
    scripts=['gcimagebundle'],
    test_suite='gcimagebundlelib.tests',
)
