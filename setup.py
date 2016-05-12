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

import setuptools


# NOTE Not yet able to build a working deb or rpm. Will build a working
# python package.


setuptools.setup(
    name='google_compute_engine',
    version='2.0.0',
    author='Google Compute Engine Team',
    author_email='gc-team@google.com',
    url='https://github.com/GoogleCloudPlatform/compute-image-packages',

    description='Google Compute Engine',
    long_description='Google Compute Engine guest environment.',
    install_requires=['boto>=2.25.0'],
    license='Apache Software License',

    packages=setuptools.find_packages(),

    # These end up in /usr/bin
    scripts=[
        'scripts/optimize_local_ssd',
        'scripts/set_hostname',
        'scripts/set_multiqueue',
    ],

    # These end up in /usr/bin, for example /usr/bin/google_accounts_daemon
    entry_points={
        'console_scripts': [
            'google_accounts_daemon=accounts.accounts_daemon:main',
            'google_clock_skew_daemon=clock_skew.clock_skew_daemon:main',
            'google_ip_forwarding_daemon=ip_forwarding.ip_forwarding_daemon:main',
            'google_instance_setup=instance_setup.instance_setup:main',
            'google_metadata_script_runner=metadata_scripts.script_manager:main',
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
