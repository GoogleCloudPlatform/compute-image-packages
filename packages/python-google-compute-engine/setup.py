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

import sys

import setuptools

install_requires = ['setuptools']
if sys.version_info < (3, 0):
  install_requires += ['boto']
if sys.version_info >= (3, 7):
  install_requires += ['distro']

setuptools.setup(
    author='Google Compute Engine Team',
    author_email='gc-team@google.com',
    description='Google Compute Engine',
    include_package_data=True,
    install_requires=install_requires,
    license='Apache Software License',
    long_description='Google Compute Engine guest environment.',
    name='google-compute-engine',
    packages=setuptools.find_packages(),
    url='https://github.com/GoogleCloudPlatform/compute-image-packages',
    version='20200113.0',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
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
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Internet',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
