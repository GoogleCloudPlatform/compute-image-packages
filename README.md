## Linux Guest Environment for Google Compute Engine

[![Build Status](https://travis-ci.org/GoogleCloudPlatform/compute-image-packages.svg?branch=master)](https://travis-ci.org/GoogleCloudPlatform/compute-image-packages) [![codecov](https://codecov.io/gh/GoogleCloudPlatform/compute-image-packages/branch/master/graph/badge.svg)](https://codecov.io/gh/GoogleCloudPlatform/compute-image-packages)

This repository stores the collection of packages installed on Google supported
Compute Engine [images](https://cloud.google.com/compute/docs/images).

**Table of Contents**

* [Background](#background)
* [Guest Overview](#guest-overview)
* [Common Libraries](#common-libraries)
    * [Metadata Watcher](#metadata-watcher)
    * [Logging](#logging)
    * [Configuration Management](#configuration-management)
    * [File Management](#file-management)
    * [Network Utilities](#network-utilities)
* [Daemons](#daemons)
    * [Accounts](#accounts)
    * [Clock Skew](#clock-skew)
    * [IP Forwarding](#ip-forwarding)
* [Instance Setup](#instance-setup)
* [Metadata Scripts](#metadata-scripts)
* [Network Setup](#network-setup)
* [Configuration](#configuration)
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

## Guest Overview

The guest environment is made up of the following components:

*   **Accounts** daemon to setup and manage user accounts, and to enable SSH key
    based authentication.
*   **Clock skew** daemon to keep the system clock in sync after VM start and
    stop events.
*   **Disk expand** scripts to expand the VM root partition for CentOS 6,
    CentOS 7, RHEL 6, and RHEL 7 images.
*   **Instance setup** scripts to execute VM configuration scripts during boot.
*   **IP forwarding** daemon that integrates network load balancing with
    forwarding rule changes into the guest.
*   **Metadata scripts** to run user-provided scripts at VM startup and
    shutdown.
*   **Network setup** service to enable multiple network interfaces on boot.

The Linux guest environment is written in Python and is version agnostic
between Python 2.6 and 3.5. There is complete unittest coverage for every Python
library and script. The design of various guest libraries, daemons, and scripts,
are detailed in the sections below.

## Common Libraries

The Python libraries are shared with each of the daemons and the instance setup
tools.

#### Metadata Watcher

The guest environment relies upon retrieving content from the metadata server to
configure the VM environment. A metadata watching library handles all
communication with the metadata server.

The library exposes two functions:

*   **GetMetadata** immediately retrieves the contents of the metadata server
    for a given metadata key. The function catches and logs any connection
    related exceptions. The metadata server content is returned as a
    deserialized JSON object.
*   **WatchMetadata** continuously makes a hanging GET, watching for changes to
    the specified contents of the metadata server. When the request closes, the
    watcher verifies the etag was updated. In case of an update, the etag is
    updated and a provided handler function is called with the deserialized JSON
    metadata content. The WatchMetadata function should never terminate; it
    catches and logs any connection related exceptions, and catches and logs any
    exception generated from calling the handler.

Metadata server requests have custom retry logic for metadata server
unavailability; by default, any request has one minute to complete before the
request is cancelled. In case of a brief network outage where the metadata
server is unavailable, there is a short delay between retries.

#### Logging

The Google added daemons and scripts write to the serial port for added
transparency. A common logging library is a thin wrapper around the Python
logging module. The library configures appropriate SysLog handlers, sets the
logging formatter, and provides a debug options for added logging and console
output.

#### Configuration Management

A configuration file allows users to disable daemons and modify instance setup
behaviors from a single location. Guest environment daemons and scripts need a
mechanism to integrate user settings into the guest. A configuration management
library retrieves and modifies these settings.

The library exposes the following functions:

*   **GetOptionString** retrieves the value for a configuration option. The type
    of the value is a string if set.
*   **GetOptionBool** retrieves the value for a configuration option. The type
    of the value is a boolean if set.
*   **SetOption** sets the value of an option in the config file. An overwrite
    flag specifies whether to replace an existing value.
*   **WriteConfig** writes the configuration values to a file. The function is
    responsible for locking the file, preventing concurrent writes, and writing
    a file header if one is provided.

#### File Management

Guest environment daemons and scripts use a common library for file management.
The library provides the following functions:

*   **SetPermissions** unifies the logic to set permissions and simplify file
    creation across the various Linux distributions. The function sets the mode,
    UID, and GID, of a provided path. On supported OS configurations that user
    SELinux, the SELinux context is automatically set.
*   **LockFile** is a context manager that simplifies the process of file
    locking in Python. The function sets up an `flock` and releases the lock on
    exit.

#### Network Utilities

A network-utilities library retrieves information about a network interface. The
library is used for IP forwarding and for setting up an Ethernet interface on
boot. The library exposes a `GetNetworkInterface` function that retrieves the
network interface name associated with a MAC address.

## Daemons

The guest environment daemons import and use the common libraries described
above. Each daemon reads the configuration file before execution. This allows a
user to easily disable undesired functionality. Additional daemon behaviors are
detailed below.

#### Accounts

The accounts daemon is responsible for provisioning and deprovisioning user
accounts. The daemon grants permissions to user accounts, and updates the list
of authorized keys that have access to accounts based on metadata SSH key
updates. User account creation is based on
[adding and remove SSH Keys](https://cloud.google.com/compute/docs/instances/adding-removing-ssh-keys)
stored in metadata.

The accounts management daemon has the following behaviors.

*   Administrator permissions are managed with a `google-sudoers` Linux group.
*   All users provisioned by the account daemon are added to the
    `google-sudoers` group.
*   The daemon stores a file in the guest to preserve state for the user
    accounts managed by Google.
*   The authorized keys file for a Google managed user is deleted when all SSH
    keys for the user are removed from metadata.
*   User accounts not managed by Google are not modified by the accounts daemon.

#### Clock Skew

The clock skew daemon is responsible for syncing the software clock with the
hypervisor clock after a stop/start event or after a migration. Preventing clock
skew may result in `system time has changed` messages in VM logs.

#### IP Forwarding

The IP forwarding daemon uses IP forwarding metadata to setup or remove IP
routes in the guest.

*   Only IPv4 IP addresses are currently supported.
*   Routes are set on the default Ethernet interface determined dynamically.
*   Google routes are configured, by default, with the routing protocol ID `66`.
    This ID is a namespace for daemon configured IP addresses.

## Instance Setup

Instance setup runs during VM boot. The script configures the Linux guest
environment by performing the following tasks.

*   Optimize for local SSD.
*   Enable multi-queue on all the virtionet devices.
*   Wait for network availability.
*   Set SSH host keys the first time the instance is booted.
*   Set the `boto` config for using Google Cloud Storage.
*   Create the defaults configuration file.

The defaults configuration file incorporates any user provided setting in
`/etc/default/instance_configs.cfg.template` and does not override other
conflicting settings. This allows package updates without overriding user
configuration.

## Metadata Scripts

Metadata scripts implement support for running user provided
[startup scripts](https://cloud.google.com/compute/docs/startupscript) and
[shutdown scripts](https://cloud.google.com/compute/docs/shutdownscript). The
guest support for metadata scripts is implemented in Python with the following
design details.

*   Metadata scripts are executed in a shell.
*   If multiple metadata keys are specified (e.g. `startup-script` and
    `startup-script-url`) both are executed.
*   If multiple metadata keys are specified (e.g. `startup-script` and
    `startup-script-url`) a URL is executed first.
*   The exit status of a metadata script is logged after completed execution.

## Network Setup

A network setup service runs on boot and enables all associated network
interfaces. Network interfaces are specified by MAC address in instance
metadata.

## Configuration

Users of Google provided images may configure the guest environment behaviors
using a configuration file. To make configuration changes, add settings to
`/etc/default/instance_configs.cfg.template`. If you are attempting to change
the behavior of a running instance, run `/usr/bin/google_instance_setup` before
reloading the affected daemons.

Linux distributions looking to include their own defaults can specify settings
in `/etc/default/instance_configs.cfg.distro`. These settings will not override
`/etc/default/instance_configs.cfg.template`. This enables distribution settings
that do not override user configuration during package update.

The following are valid user configuration options.

Section           | Option                 | Value
----------------- | ---------------------- | -----
Accounts          | deprovision\_remove    | `true` makes deprovisioning a user destructive.
Accounts          | groups                 | Comma separated list of groups for newly provisioned users.
Accounts          | useradd\_cmd           | Command string to create a new user.
Accounts          | userdel\_cmd           | Command string to delete a user.
Accounts          | usermod\_cmd           | Command string to modify a user's groups.
Accounts          | groupadd\_cmd          | Command string to create a new group.
Daemons           | accounts\_daemon       | `false` disables the accounts daemon.
Daemons           | clock\_skew\_daemon    | `false` disables the clock skew daemon.
Daemons           | ip\_forwarding\_daemon | `false` disables the IP forwarding daemon.
InstanceSetup     | host\_key\_types       | Comma separated list of host key types to generate.
InstanceSetup     | optimize\_local\_ssd   | `false` prevents optimizing for local SSD.
InstanceSetup     | network\_enabled       | `false` skips instance setup functions that require metadata.
InstanceSetup     | set\_boto\_config      | `false` skips setting up a `boto` config.
InstanceSetup     | set\_host\_keys        | `false` skips generating host keys on first boot.
InstanceSetup     | set\_multiqueue        | `false` skips multiqueue driver support.
IpForwarding      | ethernet\_proto\_id    | Protocol ID string for daemon added routes.
IpForwarding      | ip\_aliases            | `false` disables setting up alias IP routes.
IpForwarding      | target\_instance\_ips  | `false` disables internal IP address load balancing.
MetadataScripts   | run\_dir               | String base directory where metadata scripts are executed.
MetadataScripts   | startup                | `false` disables startup script execution.
MetadataScripts   | shutdown               | `false` disables shutdown script execution.
NetworkInterfaces | dhclient\_script       | String path to a dhclient script used by dhclient.
NetworkInterfaces | dhcp\_command          | String to execute to enable network interfaces.
NetworkInterfaces | setup                  | `false` disables network interface setup.

Setting `network_enabled` to `false` will skip setting up host keys and the
`boto` config in the guest. The setting may also prevent startup and shutdown
script execution.

## Packaging

The guest Python code is packaged as a
[compliant PyPI Python package](http://python-packaging-user-guide.readthedocs.io/en/latest/)
that can be used as a library or run independently. In addition to the Python
package, deb and rpm packages are created with appropriate init configuration
for supported GCE distros. The packages are targeted towards distribution
provided Python versions.

Distro       | Package Type | Python Version | Init System
------------ | ------------ | -------------- | -----------
Debian 8     | deb          | 2.7            | systemd
Debian 9     | deb          | 3.5 or 2.7     | systemd
CentOS 6     | rpm          | 2.6            | upstart
CentOS 7     | rpm          | 2.7            | systemd
RHEL 6       | rpm          | 2.6            | upstart
RHEL 7       | rpm          | 2.7            | systemd
Ubuntu 14.04 | deb          | 2.7            | upstart
Ubuntu 16.04 | deb          | 3.5 or 2.7     | systemd
SLES 11      | rpm          | 2.6            | sysvinit
SLES 12      | rpm          | 2.7            | systemd

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

The package source for Debian and RPM specs for Enterprise Linux 6 and 7 are
included in this project. There are also
[Daisy](https://github.com/GoogleCloudPlatform/compute-image-tools/tree/master/daisy)
workflows for spinning up GCE VM's to automatically build the packages for
Debian, Red Hat, and CentOS. See the [README](packaging/README.md) in the
packaging directory for more details.

#### Version Updates

There are several places where package versions have to be updated and must
match to successfully release an update.

* `setup.py` Update the version string with the Python package version. Used
  for entry points through the Python egg and PyPI.
* `specs/google-compute-engine.spec` Update the version of the
  `google-compute-engine` package for EL6 and EL7.
* `specs/python-google-compute-engine.spec` Update the version string of the
  `python-google-compute-engine` package for EL6 and EL7.
* `debian/changelog` Update `google-compute-image-packages (VERSION) stable`,
  the version of the Debian packages.
* Update the variable `package_version` when invoking the package build workflows.

#### Package Distribution

The deb and rpm packages used in some GCE images are published to Google Cloud
repositories. Debian 8 and 9, CentOS 6 and 7, and RHEL 6 and 7 use these
repositories to install and update the `google-compute-engine`, and
`python-google-compute-engine` (and `python3-google-compute-engine` for Python 3)
packages. If you are creating a custom image, you can also use these repositories
in your image.

**For Debian 8, run the following commands as root:**

Add the public repo key to your system:
```
curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key add -
```

Add a source list file `/etc/apt/sources.list.d/google-cloud.list`:
```
tee /etc/apt/sources.list.d/google-cloud.list << EOM
deb http://packages.cloud.google.com/apt google-compute-engine-jessie-stable main
deb http://packages.cloud.google.com/apt google-cloud-packages-archive-keyring-jessie main
EOM
```

Install the packages to maintain the public key over time:
```
apt-get update; apt-get install google-cloud-packages-archive-keyring
```

Install the `google-compute-engine` and `python-google-compute-engine` packages:
```
apt-get update; apt-get install -y google-compute-engine python-google-compute-engine
```

**For Debian 9, run the following commands as root:**

Add the public repo key to your system:
```
curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key add -
```

Add a source list file `/etc/apt/sources.list.d/google-cloud.list`:
```
tee /etc/apt/sources.list.d/google-cloud.list << EOM
deb http://packages.cloud.google.com/apt google-compute-engine-stretch-stable main
deb http://packages.cloud.google.com/apt google-cloud-packages-archive-keyring-stretch main
EOM
```

Install the packages to maintain the public key over time:
```
apt-get update; apt-get install google-cloud-packages-archive-keyring
```

Install the `google-compute-engine` and `python-google-compute-engine` packages:
```
apt-get update; apt-get install -y google-compute-engine python-google-compute-engine
```

**For EL6 and EL7 based distributions, run the following commands as root:**

Add the yum repo to a repo file `/etc/yum.repos.d/google-cloud.repo` for either
EL6 or EL7. Change `DIST` to either 6 or 7 respectively:
```
DIST=7
tee /etc/yum.repos.d/google-cloud.repo << EOM
[google-cloud-compute]
name=Google Cloud Compute
baseurl=https://packages.cloud.google.com/yum/repos/google-cloud-compute-el${DIST}-x86_64
enabled=1
gpgcheck=1
repo_gpgcheck=1
gpgkey=https://packages.cloud.google.com/yum/doc/yum-key.gpg
       https://packages.cloud.google.com/yum/doc/rpm-package-key.gpg
EOM
```

Install the `google-compute-engine`, `python-google-compute-engine` packages:
```
yum install -y google-compute-engine python-google-compute-engine
```

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
