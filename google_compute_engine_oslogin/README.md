## OS Login Support for Google Compute Engine Guest OS

This package enables Google OS Login features on Google Compute Engine
instances.

**Table of Contents**

* [Overview](#overview)
* [Components](#components)
    * [Authorized Keys Command](#authorized-keys-command)
    * [NSS Module](#nss-module)
    * [PAM Module](#pam-module)
    * [Utils](#utils)
* [Utilities](#utilities)
    * [bin dir](#bin-dir)
    * [packaging dir](#packaging-dir)
    * [policy dir](#policy-dir)
* [Packaging](#packaging)
    * [DEB](#deb)
    * [RPM](#rpm)
* [Version Updates](#version-updates)

## Overview

The OS Login package has the following components:

*   **Authorized Keys Command** to fetch SSH Keys from the user's OS Login
    Profile and make them available to sshd.
*   **NSS Module** provides support for making user & group information
    available to the system from the OS Login Profile, using NSS (Name Service
    Switch) functionality.
*   **PAM Module** provides authorization and authentication support allowing
    the system to use data stored in Google IAM permissions to control both the
    ability to log into an instance and to perform operations as root (sudo).
*   **Utils** provides common code to support the components listed above.

In addition to the main components, there are also utilities for packaging and
installing these components:

*   **bin** contains a shell script for activating/deactivating the package
    components.
*   **packaging** contains files used to generate `.deb` and `.rpm` packages for
    the OS Login components.
*   **policy** contains SELinux "type enforcement" files for configuring SELinux
    on CentOS/RHEL systems.


## Components


#### Authorized Keys Command

The `google_authorized_keys` binary is designed to be uses with sshd's
"AuthorizedKeysCommand" option in `sshd_config`. It does the following:

*   Reads the user's profile information from Metadata server at
    `http://metadata.google.internal/computeMetadata/v1/oslogin/users?username=<username>`
*   Checks to make sure that the user is authorized to log in at
    `http://metadata.google.internal/computeMetadata/v1/oslogin/authorize?email=<user_email>&policy=login`
*   If the check is successful, return a list of SSH keys from the profile for
    use by sshd.

#### NSS Module

The `nss_oslogin` module is built and installed in the appropriate `lib`
directory as a shared object with the name `libnss_oslogin.so.2`. It is then
activated by an `oslogin` entry in /etc/nsswitch.conf. It does the following:

*   Adds support for looking up `passwd` (e.g. `getent passwd` entries from
    the Metadata server depending on what is being requested.
*   For returning a list of all users, it will read from
    `http://metadata.google.internal/computeMetadata/v1/oslogin/users`
*   For looking up a user by username, it will read from
    `http://metadata.google.internal/computeMetadata/v1/oslogin/users?username=<username>`
*   For looking up a user by UID, it will read from
    `http://metadata.google.internal/computeMetadata/v1/oslogin/users?uid=<uid>`

#### PAM Module

The `pam_module` directory contains two modules used by Linux PAM (Pluggable
Authentication Modules).

The first module, `pam_oslogin_login.so`, determines whether a given user is
allowed to SSH into an instance. It is activated by adding an `account requisite`
line to the PAM sshd config file. It does the following:

*   Checks to see if the user is an OS Login user at
    `http://metadata.google.internal/computeMetadata/v1/oslogin/users?username=<username>`
*   If the user is an OS Login user (as opposed to a local user), a check is
    made to confirm whether the user has permissions to SSH into the instance at
    `http://metadata.google.internal/computeMetadata/v1/oslogin/authorize?email=<user_email>&policy=login`
*   If the user has authorization, or the user is not an OS Login user, a
    success message will be returned and SSH can proceed. Otherwise, a denied
    message will be returned and the SSH check will fail.

The second module, `pam_oslogin_admin.so`, determines whether a given user
should have admin (sudo) permissions on the instance. It is activated by adding
an `account optional` line to the PAM sshd config file. It does the following:

*   Checks to see if the user is an OS Login user at
    `http://metadata.google.internal/computeMetadata/v1/oslogin/users?username=<username>`
*   If the user is not an OS Login user, nothing is done and the module exits
    with success.
*   If the user is an OS Login user, a check is made to see if the user should
    have admin permissions at
    `http://metadata.google.internal/computeMetadata/v1/oslogin/authorize?email=<user_email>&policy=adminLogin`
*   If the user should have admin permission, a file is added to
    `/var/google-sudoers.d/` named with the username giving that user sudo
    privileges.
*   If the user should not have admin permissions, the file is removed from
    `/var/google-sudoers.d/` if it exists.

#### Utils

`oslogin_utils` contains common functions for things like HTTP calls,
interacting with the Metadata server and parsing JSON objects.


## Utilities

#### bin dir

The `bin` directory contains a shell script called `google_oslogin_control` that
is used to activate or deactivate the OS Login features. It is called in the pre
and post install scripts in the `.deb` and `.rpm` packages. It does the
following:

*   Adds (or removes) the AuthorizedKeysCommand and AuthorizedKeysCommandUser
    lines to (from) `sshd_config` and restarts sshd.
*   Adds (or removes) `oslogin` to (from) nsswitch.conf
*   Adds (or removes) the `account` entries to (from) the PAM sshd config. Also
    adds (or removes) the pam_mkhomedir.so module to automatically create home
    directorys for OS Login users.
*   Creates (or deletes) the `/var/google-sudoers.d/` directory and a file
    called `google-oslogin` in `/etc/sudoers.d/` to include the directory.

#### packaging dir

The `packaging` directory contains files for creating `.deb` and `.rpm`
packages. See [Packaging](#packaging) for details.

#### policy dir

The `policy` directory contains `.te` (type enforcement) files used by SELinux
to give the OS Login features the appropriate SELinux permissions. These are
compiled using `checkmodule` and `semodule_package` to create an `oslogin.pp`
that is intstalled in the appropriate SELinux directory.

## Packaging

There is currently support for creating packages for the following distros:
* Debian 8
* Debian 9
* CentOS/RHEL 6
* CentOS/RHEL 7

#### DEB

_Note: In the packaging directory, there is a script called `setup_deb.sh` which
performs these steps, but it is not a production-quality script._

The basic steps for creating a .deb package are:

*   Install necessary dependencies: make, g++, libcurl4-openssl-dev,
    libjson-c-dev, libpam-dev
*   Install `.deb` creation tools: debhelper, devscripts, build-essential
*   Create a compressed tar file named
    `google-compute-engine-oslogin_M.M.R.orig.tar.gz` using the files in this
    directory, excluding the `packaging` directory (where M.M.R is the version
    number).
*   In a separate directory, extract the `.orig.tar.gz` file and then copy the
    appropriate `debian` directory into the top level. (e.g. When working on
    Debian 8, copy the `debian8` directory to a directory named `debian` within
    the code directory.
*   Run `debbuild -us -uc` to build the package.

#### RPM

_Note: In the packaging directory, there is a script called `setup_rpm.sh`
which performs these steps, but it is not a production-quality script._

*   Install necessary dependencies: make, gcc-c++ libcurl-devel, json-c,
    json-c-devel, pam-devel, policycoreutils-python
*   Install `.rpm` creation tools: rpmdevtools
*   Create a compressed tar file named
    `google-compute-engine-oslogin_M.M.R.orig.tar.gz` using the files in this
    directory, excluding the `packaging` directory (where M.M.R is the version
    number).
*   In a separate location, create a directory called `rpmbuild` and a
    subdirectory called `SOURCES`. Copy the `.orig.tar.gz` file into the
    `SOURCES` directory.
*   Copy the `SPECS` directory from the `rpmbuild` directory here into the
    `rpmbuild` directory you created.
*   Run `rpmbuild --define "_topdir /path/to/rpmbuild" -ba
    /path/to/rpmbuild/SPECS/google-compute-engine-oslogin.spec` to build the
    package.


## Version Updates

When updating version numbers, changes need to be made in a few different
places:

*   `Makefile`: Update the MAJOR, MINOR, and REVISION vars.
*   `packaging/debian8/changelog`: Add a new entry with the new version.
*   `packaging/debian9/changelog`: Add a new entry with the new version.
*   `packaging/debian8/google-compute-engine-oslogin.links`: Update the libnss
    version string.
*   `packaging/debian9/google-compute-engine-oslogin.links`: Update the libnss
    version string.
*   `packaging/rpmbuild/SPECS/google-compute-engine-oslogin.spec`: Update the
    "Version:" field.
*   `packaging/setup_deb.sh`: Update VERSION var.
*   `packaging/setup_rpm.sh`: Update VERSION var.
