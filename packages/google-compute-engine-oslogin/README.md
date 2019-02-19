## OS Login Guest Environment for Google Compute Engine

This package enables Google Cloud OS Login features on Google Compute Engine
instances.

**Table of Contents**

* [Overview](#overview)
* [Components](#components)
    * [Authorized Keys Command](#authorized-keys-command)
    * [NSS Module](#nss-module)
    * [PAM Module](#pam-module)
    * [Utils](#utils)
* [Utility Directories](#utility-directories)
    * [bin](#bin)
    * [packaging](#packaging)
    * [policy](#policy)
* [Source Packages](#source-packages)
    * [DEB](#deb)
    * [RPM](#rpm)
* [Version Updates](#version-updates)

## Overview

The OS Login package has the following components:

*   **Authorized Keys Command** to fetch SSH keys from the user's OS Login
    profile and make them available to sshd.
*   **NSS Module** provides support for making OS Login user and group
    information available to the system, using NSS (Name Service Switch)
    functionality.
*   **PAM Module** provides authorization and authentication support allowing
    the system to use data stored in Google Cloud IAM permissions to control
    both, the ability to log into an instance, and to perform operations as root
    (sudo).
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

The `google_authorized_keys` binary is designed to be used with the sshd
[AuthorizedKeysCommand](https://linux.die.net/man/5/sshd_config) option in
`sshd_config`. It does the following:

*   Reads the user's profile information from the metadata server.
    ```
    http://metadata.google.internal/computeMetadata/v1/oslogin/users?username=<username>
    ```
*   Checks to make sure that the user is authorized to log in.
    ```
    http://metadata.google.internal/computeMetadata/v1/oslogin/authorize?email=<user_email>&policy=login
    ```
*   If the check is successful, returns the SSH keys associated with the user
    for use by sshd.

#### NSS Module

The `nss_oslogin` module is built and installed in the appropriate `lib`
directory as a shared object with the name `libnss_oslogin.so.2`. The module is
then activated by an `oslogin` entry in `/etc/nsswitch.conf`. The NSS module
supports looking up `passwd` entries from the metadata server via
`getent passwd`.

*   To return a list of all users, the NSS module queries:
    ```
    http://metadata.google.internal/computeMetadata/v1/oslogin/users?pagesize=<pagesize>
    ```
*   To look up a user by username, the NSS module queries:
    ```
    http://metadata.google.internal/computeMetadata/v1/oslogin/users?username=<username
    ```
*   To look up a user by UID, the NSS module queries:
    ```
    http://metadata.google.internal/computeMetadata/v1/oslogin/users?uid=<uid>
    ```

#### PAM Module

The `pam_module` directory contains two modules used by Linux PAM (Pluggable
Authentication Modules).

The first module, `pam_oslogin_login.so`, determines whether a given user is
allowed to SSH into an instance. It is activated by adding an
`account requisite` line to the PAM sshd config file and does the following:

*   Retrieves the user's profile information from the metadata server.
    ```
    http://metadata.google.internal/computeMetadata/v1/oslogin/users?username=<username>
    ```
*   If the user has OS Login profile information (as opposed to a local user
    account), confirms whether the user has permissions to SSH into the
    instance.
    ```
    http://metadata.google.internal/computeMetadata/v1/oslogin/authorize?email=<user_email>&policy=login
    ```
*   If the user is a local user account or is authorized, PAM returns a success
    message and SSH can proceed. Otherwise, PAM returns a denied message and the
    SSH check will fail.

The second module, `pam_oslogin_admin.so`, determines whether a given user
should have admin (sudo) permissions on the instance. It is activated by adding
an `account optional` line to the PAM sshd config file and does the following:

*   Retrieves the user's profile information from the metadata server.
    ```
    http://metadata.google.internal/computeMetadata/v1/oslogin/users?username=<username>
    ```
*   If the user is a local user account, the module exits with success.
*   If the user is an OS Login user, the module perform an authorization check
    to determine if the user has admin permissions.
    ```
    http://metadata.google.internal/computeMetadata/v1/oslogin/authorize?email=<user_email>&policy=adminLogin
    ```
*   If the user is authorized as an admin, a file with the username is added to
    `/var/google-sudoers.d/`. The file gives the user sudo privileges.
*   If the authorization check fails for admin permissions, the file is removed
    from `/var/google-sudoers.d/` if it exists.

#### Utils

`oslogin_utils` contains common functions for making HTTP calls,
interacting with the metadata server, and for parsing JSON objects.

## Utility Directories

#### bin

The `bin` directory contains a shell script called `google_oslogin_control` that
activates or deactivates the OS Login features. It is called in the pre and post
install scripts in the `.deb` and `.rpm` packages. The control file performs the
following tasks:

*   Adds (or removes) AuthorizedKeysCommand and AuthorizedKeysCommandUser lines
    to (from) `sshd_config` and restarts sshd.
*   Adds (or removes) `oslogin` to (from) `nsswitch.conf`.
*   Adds (or removes) the `account` entries to (from) the PAM sshd config. Also
    adds (or removes) the `pam_mkhomedir.so` module to automatically create the
    home directory for an OS Login user.
*   Creates (or deletes) the `/var/google-sudoers.d/` directory, and a file
    called `google-oslogin` in `/etc/sudoers.d/` that includes the directory.

#### packaging

The `packaging` directory contains files for creating `.deb` and `.rpm`
packages. See [Source Packages](#source-packages) for details.

#### policy

The `policy` directory contains `.te` (type enforcement) files used by SELinux
to give the OS Login features the appropriate SELinux permissions. These are
compiled using `checkmodule` and `semodule_package` to create an `oslogin.pp`
that is intstalled in the appropriate SELinux directory.

## Source Packages

There is currently support for creating packages for the following distros:
*   Debian 8
*   Debian 9
*   CentOS/RHEL 6
*   CentOS/RHEL 7

#### DEB

_Note: the `packaging/setup_deb.sh` script performs these steps, but is not
production quality._

1.  Install build dependencies:
    ```
    sudo apt-get -y install make g++ libcurl4-openssl-dev libjson-c-dev libpam-dev
    ```
1.  Install deb creation tools:
    ```
    sudo apt-get -y install debhelper devscripts build-essential
    ```
1.  Create a compressed tar file named
    `google-compute-engine-oslogin_M.M.R.orig.tar.gz` using the files in this
    directory, excluding the `packaging` directory (where M.M.R is the version
    number).
1.  In a separate directory, extract the `.orig.tar.gz` file and copy the
    appropriate `debian` directory into the top level. (e.g. When working on
    Debian 8, copy the `debian8` directory to a directory named `debian` within
    the code directory.)
1.  To build the package, run the command
    ```
    debuild -us -uc
    ```

#### RPM

_Note: the `packaging/setup_rpm.sh` script performs these steps, but is not
production quality._

1.  Install build dependencies:
    ```
    sudo yum -y install make gcc-c++ libcurl-devel json-c json-c-devel pam-devel policycoreutils-python
    ```
1.  Install rpm creation tools:
    ```
    sudo yum -y install rpmdevtools
    ```
1.  Create a compressed tar file named
    `google-compute-engine-oslogin_M.M.R.orig.tar.gz` using the files in this
    directory, excluding the `packaging` directory (where M.M.R is the version
    number).
1.  In a separate location, create a directory called `rpmbuild` and a
    subdirectory called `SOURCES`. Copy the `.orig.tar.gz` file into the
    `SOURCES` directory.
1.  Copy the `SPECS` directory from the `rpmbuild` directory here into the
    `rpmbuild` directory you created.
1.  To build the package, run the command:
    ```
    rpmbuild --define "_topdir /path/to/rpmbuild" -ba /path/to/rpmbuild/SPECS/google-compute-engine-oslogin.spec
    ```
