## OS Login Guest Environment for Google Compute Engine

This repository contains the system components responsible for providing Google
Cloud OS Login features on Google Compute Engine instances.

**Table of Contents**

* [Overview](#overview)
* [Components](#components)
    * [Authorized Keys Command](#authorized-keys-command)
    * [NSS Modules](#nss-modules)
    * [PAM Modules](#pam-modules)
* [Utilities](#Utilities)
    * [Control Script](#control-script)
    * [SELinux Policy](#selinux-policy)
* [Source Packages](#source-packages)
    * [DEB](#deb)
    * [RPM](#rpm)

## Overview

The OS Login Guest Environment consists of the following main components:

*   **Authorized Keys Command** which provides SSH keys from the user's OS Login
    profile to sshd for authenticating users at login.
*   **NSS Modules** which provide support for making OS Login user and group
    information available to the system, using NSS (Name Service Switch)
    functionality.
*   **PAM Modules** which provide authorization (and authentication if
    two-factor support is enabled) support allowing the system to use Google
    Cloud IAM permissions to control the ability to log into an instance or to
    perform operations as root (via `sudo`).

In addition to the main components, there are also the following utilities:

*   **google_oslogin_control** is a shell script for activating/deactivating the
    OS Login components.
*   **google_oslogin_nss_cache** is a utility for updating the local user and
    group cache.
*   **selinux** contains SELinux policy definition files and a compiled policy
    package for configuring SELinux to support OS Login.

The **packaging** directory also contains files used to generate `.deb` and
`.rpm` packages for the OS Login components.

## Components

#### Authorized Keys Command

The `google_authorized_keys` binary is designed to be used with the sshd
`AuthorizedKeysCommand` option in [sshd_config(5)](https://linux.die.net/man/5/sshd_config).
It does the following:

*   Reads the user's profile information from the metadata server:
    ```
    http://metadata.google.internal/computeMetadata/v1/oslogin/users?username=<username>
    ```
*   Checks to make sure that the user is authorized to log in:
    ```
    http://metadata.google.internal/computeMetadata/v1/oslogin/authorize?email=<user_email>&policy=login
    ```
*   If the check is successful, returns the SSH keys associated with the user
    for use by sshd. Otherwise, exits with an error code.

#### NSS Modules

`libnss_oslogin.so` and `libnss_cache_oslogin.so` are NSS service modules which
make OS Login users and groups available for use on the local system. The module
is activated by adding `oslogin` and `cache_oslogin` entries for services in
[nsswitch.conf(5)](https://linux.die.net/man/5/nsswitch.conf).

*   To return a list of all users, the NSS module queries:
    ```
    http://metadata.google.internal/computeMetadata/v1/oslogin/users?pagesize=<pagesize>
    ```
*   To look up a user by username, the NSS module queries:
    ```
    http://metadata.google.internal/computeMetadata/v1/oslogin/users?username=<username>
    ```
*   To look up a user by UID, the NSS module queries:
    ```
    http://metadata.google.internal/computeMetadata/v1/oslogin/users?uid=<uid>
    ```

#### PAM Modules

`pam_oslogin_login.so` is a PAM module which determines whether a given user is
allowed to SSH into an instance.

It is activated by adding an entry for the account group to the PAM service
config for sshd as:
   ```
   account requisite pam_oslogin_login.so
   ```

This module:

*   Retrieves the user's profile information from the metadata server:
    ```
    http://metadata.google.internal/computeMetadata/v1/oslogin/users?username=<username>
    ```
*   If the user does not have OS Login profile information it is passed on to
    the system authentication modules to be processed as a local user.
*   Otherwise, the module confirms whether the user has permissions to SSH into
    the instance:
    ```
    http://metadata.google.internal/computeMetadata/v1/oslogin/authorize?email=<user_email>&policy=login
    ```
*   If the user is authorized, PAM returns a success message and SSH can
    proceed. Otherwise, PAM returns a denied message and the SSH check will
    fail.

`pam_oslogin_admin.so` is a PAM module which determines whether a given user
should have admin (sudo) permissions on the instance.

It is activated by adding an entry for the `account` group to the PAM service
config for sshd config as:
   ```
   account optional pam_oslogin_admin.so
   ```

This module:

*   Retrieves the user's profile information from the metadata server.
    ```
    http://metadata.google.internal/computeMetadata/v1/oslogin/users?username=<username>
    ```
*   If the user is not an OS Login user (a local user account), the module
    returns success.
*   Otherwise, the module determines if the user has admin permissions:
    ```
    http://metadata.google.internal/computeMetadata/v1/oslogin/authorize?email=<user_email>&policy=adminLogin
    ```
*   If the user is authorized as an admin, a file with the username is added to
    `/var/google-sudoers.d/`. The file gives the user sudo privileges.
*   If the authorization check fails for admin permissions, the file is removed
    from `/var/google-sudoers.d/` if it exists.

## Utilities

#### Control Script

The `google_oslogin_control` shell script activates or deactivates the OS Login
features. It is invoked by the google accounts daemon. The control file performs
the following tasks:

*   Adds (or removes) AuthorizedKeysCommand and AuthorizedKeysCommandUser lines
    to (from) `sshd_config` and restarts sshd.
*   Adds (or removes) `oslogin` and `cache_oslogin` to (from) `nsswitch.conf`.
*   Adds (or removes) the `account` entries to (from) the PAM sshd config. Also
    adds (or removes) the `pam_mkhomedir.so` module to automatically create the
    home directory for an OS Login user.
*   Creates (or deletes) the `/var/google-sudoers.d/` directory, and a file
    called `google-oslogin` in `/etc/sudoers.d/` that includes the directory.

#### SELinux Policy

The `selinux` directory contains `.te` (type enforcement) and `.fc` (file
context) files used by SELinux to give the OS Login features the appropriate
SELinux permissions. These are compiled using `checkmodule` and
`semodule_package` to create an policy package `oslogin.pp`.

## Source Packages

There is currently support for creating packages for the following distros:

*   Debian 9
*   CentOS/RHEL 6
*   CentOS/RHEL 7

Files for these packages are in the `packaging/` directory.

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
    `debian` directory into the top level.
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
