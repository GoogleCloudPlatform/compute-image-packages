## Linux Guest Environment for Google Compute Engine

[![Build Status](https://travis-ci.org/GoogleCloudPlatform/compute-image-packages.svg?branch=master)](https://travis-ci.org/GoogleCloudPlatform/compute-image-packages) [![codecov](https://codecov.io/gh/GoogleCloudPlatform/compute-image-packages/branch/master/graph/badge.svg)](https://codecov.io/gh/GoogleCloudPlatform/compute-image-packages)

This repository stores the collection of packages installed on Google supported
Compute Engine [images](https://cloud.google.com/compute/docs/images).

**Table of Contents**

* [Background](#background)
* [Packaging](#packaging)
    * [Version Updates](#version-updates)
    * [Package Distribution](#package-distribution)
* [Troubleshooting](#troubleshooting)
* [Contributing](#contributing)
* [License](#license)

## Background

The Linux guest environment denotes the Google provided configuration and
tooling inside of a [Google Compute Engine](https://cloud.google.com/compute/)
(GCE) virtual machine. The
[metadata server](https://cloud.google.com/compute/docs/metadata) is a
communication channel for transferring information from a client into the guest.
The Linux guest environment includes a set of scripts and daemons (long-running
processes) that read the content of the metadata server to make a virtual
machine run properly on our platform.

## Packaging

The guest Python code is packaged as a
[compliant PyPI Python package](https://packaging.python.org/)
that can be used as a library or run independently. In addition to the Python
package, deb and rpm packages are created with appropriate init configuration
for supported GCE distros. The packages are targeted towards distribution
provided Python versions.

Distro       | Package Type | Python Version | Init System
------------ | ------------ | -------------- | -----------
SLES 12      | rpm          | 2.7            | systemd
SLES 15      | rpm          | 3.6            | systemd
CentOS 6     | rpm          | 2.6            | upstart
CentOS 7     | rpm          | 2.7            | systemd
CentOS 8     | rpm          | 3.6            | systemd
RHEL 6       | rpm          | 2.6            | upstart
RHEL 7       | rpm          | 2.7            | systemd
RHEL 8       | rpm          | 3.6            | systemd
Ubuntu 14.04 | deb          | 2.7            | upstart
Ubuntu 16.04 | deb          | 3.5 or 2.7     | systemd
Ubuntu 18.04 | deb          | 3.6            | systemd
Ubuntu 19.04 | deb          | 3.7            | systemd
Debian 9     | deb          | 3.5 or 2.7     | systemd
Debian 10    | deb          | 3.7            | systemd

We build the following packages for the Linux guest environment.

*   `google-compute-engine`
    *  System init scripts (systemd, upstart, or sysvinit).
    *  Includes udev rules, sysctl rules, rsyslog configs, dhcp configs for
       hostname setting.
    *  Entry point scripts created by the Python package located in `/usr/bin`.
    *  Includes bash scripts used by `instance_setup`.
*   `python-google-compute-engine`
    *  The Python 2 package for Linux daemons and libraries.
*   `python3-google-compute-engine`
    *  The Python 3 package for Linux daemons and libraries.
*   `google-compute-engine-oslogin`
    *  The PAM and NSS modules for [OS Login](https://cloud.google.com/compute/docs/oslogin/)
*   `gce-disk-expand`
    *  The on-boot resize scripts for root partition.

The package sources (RPM spec files and Debian packaging directories) are also
included in this project. There are also [Daisy](https://github.com/GoogleCloudPlatform/compute-image-tools/tree/master/daisy)
workflows for spinning up GCE VM's to automatically build the packages for
Debian, Red Hat, and CentOS. See the [README](packaging/README.md) in the
packaging directory for more details.

#### Version Updates

Versions are described as 1:YYYYMMDD.NN-gN, meaning epoch 1 to denote from a
distro maintained package which will be 0, a date string formatted as year,
month, day, an incrementing minor release, and gN representing the Google
package release. Debian, Ubuntu, and SUSE maintain distro packages which may be
out of date, have different versioning, or naming.

The method for making version updates differs by package.

* All packages need the `VERSION` variable set in the `setup_{deb,rpm}.sh` build
  scripts.
* All packages need the `debian/changelog` file updated. Please use `dch(1)` to
  update it.
* `python-google-compute-engine` additionally needs the version specified in
  `setup.py`. This is used for entry points through the Python egg and PyPI.
* `google-compute-engine-oslogin` needs the version also updated in the
  `Makefile`.

#### Package Distribution

The deb and rpm packages are published to Google Cloud repositories. Debian,
CentOS, and RHEL use these repositories to install and update the
`google-compute-engine`, `google-compute-engine-oslogin` and
`python-google-compute-engine` (and `python3-google-compute-engine` for Python
3) packages. If you are creating a custom image, you can also use these
repositories in your image.

**For Debian, run the following commands as root:**

Add the public repo key to your system:
```
curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -
```

Add a source list file `/etc/apt/sources.list.d/google-cloud.list` and change
`DIST` to either `stretch` for Debian 9 or `buster` for Debian 10:
```
DIST=stretch
sudo tee /etc/apt/sources.list.d/google-cloud.list << EOM
deb http://packages.cloud.google.com/apt google-compute-engine-${DIST}-stable main
deb http://packages.cloud.google.com/apt google-cloud-packages-archive-keyring-${DIST} main
EOM
```

Install the packages to maintain the public key over time:
```
sudo apt update; sudo apt install -y google-cloud-packages-archive-keyring
```

You are then able to install any of the packages from this repo.

**For RedHat based distributions, run the following commands as root:**

Add the yum repo to a repo file `/etc/yum.repos.d/google-cloud.repo` for EL6,
EL7, or EL8. Change `DIST` to either 6, 7, or 8 respectively:
```
DIST=7
tee /etc/yum.repos.d/google-cloud.repo << EOM
[google-compute-engine]
name=Google Compute Engine
baseurl=https://packages.cloud.google.com/yum/repos/google-compute-engine-el${DIST}-x86_64-stable
enabled=1
gpgcheck=1
repo_gpgcheck=1
gpgkey=https://packages.cloud.google.com/yum/doc/yum-key.gpg
       https://packages.cloud.google.com/yum/doc/rpm-package-key.gpg
EOM
```

You are then able to install any of the packages from this repo.

## Troubleshooting

**Deprecated Packages**

Deprecated Package                   | Replacement
------------------------------------ | ---------------------------------------------------------
`google-compute-engine-jessie`       | `google-compute-engine` and `python-google-compute-engine`
`google-compute-engine-stretch`      | `google-compute-engine` and `python-google-compute-engine`
`google-compute-engine-init`         | `google-compute-engine`
`google-compute-engine-init-jessie`  | `google-compute-engine`
`google-compute-engine-init-stretch` | `google-compute-engine`
`google-config`                      | `google-compute-engine`
`google-config-jessie`               | `google-compute-engine`
`google-config-stretch`              | `google-compute-engine`
`google-compute-daemon`              | `python-google-compute-engine`
`google-startup-scripts`             | `google-compute-engine`

**An old CentOS 6 image fails to install the packages with an error on SCL**

CentOS 6 images prior to `v20160526` may fail to install the package with
the error:
```
http://mirror.centos.org/centos/6/SCL/x86_64/repodata/repomd.xml: [Errno 14] PYCURL ERROR 22 - "The requested URL returned error: 404 Not Found"
```

Remove the stale repository file:
`sudo rm -f /etc/yum.repos.d/CentOS-SCL.repo`

**On some CentOS or RHEL 6 systems, extraneous python egg directories can cause
the python daemons to fail.**

In `/usr/lib/python2.6/site-packages` look for
`google_compute_engine-2.4.1-py27.egg-info` directories and
`google_compute_engine-2.5.2.egg-info` directories and delete them if you run
into this problem.

**Using boto with virtualenv**

Specific to running `boto` inside of a Python
[`virtualenv`](http://docs.python-guide.org/en/latest/dev/virtualenvs/),
virtual environments are isolated from system site-packages. This includes the
installed Linux guest environment libraries that are used to configure `boto`
credentials. There are two recommended solutions:

*   Create a virtual environment with `virtualenv venv --system-site-packages`.
*   Install `boto` via the Linux guest environment PyPI package using
    `pip install google-compute-engine`.

## Contributing

Have a patch that will benefit this project? Awesome! Follow these steps to have
it accepted.

1.  Please sign our [Contributor License Agreement](CONTRIB.md).
1.  Fork this Git repository and make your changes.
1.  Create a Pull Request against the
    [development](https://github.com/GoogleCloudPlatform/compute-image-packages/tree/development)
    branch.
1.  Incorporate review feedback to your changes.
1.  Accepted!

## License

All files in this repository are under the
[Apache License, Version 2.0](LICENSE) unless noted otherwise.
