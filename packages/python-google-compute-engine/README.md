## Python Linux Guest Environment for Google Compute Engine

This package contains the Python guest environment installed on Google supported
Compute Engine Linux [images](https://cloud.google.com/compute/docs/images).

**Table of Contents**

* [Overview](#overview)
* [Common Libraries](#common-libraries)
    * [Metadata Watcher](#metadata-watcher)
    * [Logging](#logging)
    * [Configuration Management](#configuration-management)
    * [File Management](#file-management)
    * [Network Utilities](#network-utilities)
* [Daemons](#daemons)
    * [Accounts](#accounts)
    * [Clock Skew](#clock-skew)
    * [Network](#network)
* [Instance Setup](#instance-setup)
* [Metadata Scripts](#metadata-scripts)
* [Configuration](#configuration)

## Overview

The Linux guest environment is made up of the following components:

*   **Accounts** daemon to setup and manage user accounts, and to enable SSH key
    based authentication.
*   **Clock skew** daemon to keep the system clock in sync after VM start and
    stop events.
*   **Instance setup** scripts to execute VM configuration scripts during boot.
*   **Network** daemon that handles network setup for multiple network interfaces
    on boot and integrates network load balancing with
    forwarding rule changes into the guest.
*   **Metadata scripts** to run user-provided scripts at VM startup and
    shutdown.

The Linux guest environment is written in Python and is version agnostic
between Python 2.6 and 3.7. There is complete unittest coverage for every Python
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

#### Network

The network daemon uses network interface metadata to manage the network
interfaces in the guest by performing the following tasks:

*   Enabled all associated network interfaces on boot. Network interfaces are
    specified by MAC address in instance metadata.
*   Uses IP forwarding metadata to setup or remove IP routes in the guest.
    *   Only IPv4 IP addresses are currently supported.
    *   Routes are set on the default Ethernet interface determined dynamically.
    *   Google routes are configured, by default, with the routing protocol ID
        `66`. This ID is a namespace for daemon configured IP addresses.

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
Accounts          | gpasswd\_add\_cmd      | Command string to add a user to a group.
Accounts          | gpasswd\_remove\_cmd   | Command string to remove a user from a group.
Accounts          | groupadd\_cmd          | Command string to create a new group.
Daemons           | accounts\_daemon       | `false` disables the accounts daemon.
Daemons           | clock\_skew\_daemon    | `false` disables the clock skew daemon.
Daemons           | ip\_forwarding\_daemon | `false` (deprecated) skips IP forwarding.
Daemons           | network\_daemon        | `false` disables the network daemon.
InstanceSetup     | host\_key\_types       | Comma separated list of host key types to generate.
InstanceSetup     | optimize\_local\_ssd   | `false` prevents optimizing for local SSD.
InstanceSetup     | network\_enabled       | `false` skips instance setup functions that require metadata.
InstanceSetup     | set\_boto\_config      | `false` skips setting up a `boto` config.
InstanceSetup     | set\_host\_keys        | `false` skips generating host keys on first boot.
InstanceSetup     | set\_multiqueue        | `false` skips multiqueue driver support.
IpForwarding      | ethernet\_proto\_id    | Protocol ID string for daemon added routes.
IpForwarding      | ip\_aliases            | `false` disables setting up alias IP routes.
IpForwarding      | target\_instance\_ips  | `false` disables internal IP address load balancing.
MetadataScripts   | default\_shell         | String with the default shell to execute scripts.
MetadataScripts   | run\_dir               | String base directory where metadata scripts are executed.
MetadataScripts   | startup                | `false` disables startup script execution.
MetadataScripts   | shutdown               | `false` disables shutdown script execution.
NetworkInterfaces | setup                  | `false` skips network interface setup.
NetworkInterfaces | ip\_forwarding         | `false` skips IP forwarding.
NetworkInterfaces | dhcp\_command          | String path for alternate dhcp executable used to enable network interfaces.

Setting `network_enabled` to `false` will skip setting up host keys and the
`boto` config in the guest. The setting may also prevent startup and shutdown
script execution.
