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

import setuptools


setuptools.setup(
    author='Google Compute Engine Team',
    author_email='gc-team@google.com',
    description='Google Compute Engine',
    include_package_data=True,
    install_requires=['boto', 'setuptools'],
    license='Apache Software License',
    long_description='Google Compute Engine guest environment.',
    name='google-compute-engine',
    packages=setuptools.find_packages(),
    scripts=glob.glob('scripts/*'),
    url='https://github.com/GoogleCloudPlatform/compute-image-packages',
    version='2.4.1',
    # Entry points create scripts in /usr/bin that call a function.
    entry_points={
        'console_scripts': [
            'google_accounts_daemon=google_compute_engine.accounts.accounts_daemon:main',
            'google_clock_skew_daemon=google_compute_engine.clock_skew.clock_skew_daemon:main',
            'google_ip_forwarding_daemon=google_compute_engine.ip_forwarding.ip_forwarding_daemon:main',
            'google_instance_setup=google_compute_engine.instance_setup.instance_setup:main',
            'google_network_setup=google_compute_engine.network_setup.network_setup:main',
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
