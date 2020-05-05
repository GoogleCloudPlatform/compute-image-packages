## Linux Guest Environment for Google Compute Engine

This repository historically stored the collection of packages installed on
Google supported Compute Engine [images](https://cloud.google.com/compute/docs/images).
Documentation here summarizes these packages and points to new locations for
various software components.

**Table of Contents**

* [Background](#background)
* [Packaging](#packaging)
    * [Package Distribution](#package-distribution)
* [Troubleshooting](#troubleshooting)
* [Contributing](#contributing)
* [License](#license)

## Background

The Linux guest environment comprises the Google provided configuration and
tooling inside of a [Google Compute Engine](https://cloud.google.com/compute/)
(GCE) virtual machine. The
[metadata server](https://cloud.google.com/compute/docs/metadata) is a
communication channel for transferring information from a client into the guest.
The Linux guest environment includes a set of scripts and daemons (long-running
processes) that read the content of the metadata server to make a virtual
machine run properly on our platform.

## Packaging

We build the following packages for the Linux guest environment.

*   `google-compute-engine`(located in the [guest-configs](https://github.com/GoogleCloudPlatform/guest-configs) repo)
    *  System init scripts (systemd, upstart, or sysvinit).
    *  Includes udev rules, sysctl rules, rsyslog configs, dhcp configs for
       hostname setting.
    *  Includes bash scripts used during instance setup.
    * This package depends on the other necessary packages, and can be used as
      an entry point to [install the guest environment](https://cloud.google.com/compute/docs/images/install-guest-environment).
*   `google-compute-engine-oslogin`(located in the [guest-oslogin](https://github.com/GoogleCloudPlatform/guest-oslogin) repo)
    *  The PAM and NSS modules for [OS Login](https://cloud.google.com/compute/docs/oslogin/)
*   `google-guest-agent`(located in the [guest-agent](https://github.com/GoogleCloudPlatform/guest-agent) repo)
    *  The guest agent which performs all on-guest actions needed to support GCE
       features.
*   `gce-disk-expand`(located in the [guest-diskexpand](https://github.com/GoogleCloudPlatform/guest-diskexpand) repo)
    *  The on-boot resize scripts for root partition.

The legacy [guest Python code](packages/python-google-compute-engine) is
packaged as a [compliant PyPI Python package](https://packaging.python.org/)
that can be used as a library or run independently.

#### Package Distribution

The deb and rpm packages are published to Google Cloud repositories. Debian,
CentOS, and RHEL use these repositories to install and update the
`google-compute-engine`, `google-compute-engine-oslogin` and
`google-guest-agent` packages. If you are creating a custom image, you can also
use these repositories in your image.

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

## Deprecated packages

Deprecated Package                   | Replacement
------------------------------------ | ---------------------------------------------------------
 `python-google-compute-engine`      | `google-guest-agent`
 `python3-google-compute-engine`     | `google-guest-agent`
`google-compute-engine-jessie`       | `google-compute-engine`
`google-compute-engine-stretch`      | `google-compute-engine`
`google-compute-engine-init`         | `google-compute-engine`
`google-compute-engine-init-jessie`  | `google-compute-engine`
`google-compute-engine-init-stretch` | `google-compute-engine`
`google-config`                      | `google-compute-engine`
`google-config-jessie`               | `google-compute-engine`
`google-config-stretch`              | `google-compute-engine`
`google-compute-daemon`              | `python-google-compute-engine`
`google-startup-scripts`             | `google-compute-engine`

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
