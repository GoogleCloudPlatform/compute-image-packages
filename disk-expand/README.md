## Experimental gce disk-expand package.

This package is intended to expand the root partition up to 2TB on a GCE VM. It
consists of several scripts from other packages that for various reasons are not
maintained by the distros; cloud-utils-growpart, dracut-modules-growroot, and an
upstream version of the growpart script. See below for details. This package is
being provided on an experimental basis for GCE CentOS and RHEL 6 images only at
this time.

### Build the package

A script to build the package is provided for convenience.
`./build_package.sh /OUTPUT_DIR` will yield an rpm and an srpm in the
defined output directory.

### Package usage

1. Update your distro and reboot. If there is a kernel update, you need to be
   running the new kernel for dracut to update it properly. Alternativley, if
   there is not a kernel update you can just install the gce-disk-expand
   package in the next step.
   `yum -y update ; reboot`
1. Install the gce-disk-expand package with yum and reboot:
   `yum -y install /PATH_TO/gce-disk-expand-el6-VER-DATE.x86_64.rpm ; reboot`

Your root partition will now be expanded to the full size of your disk up to
2TB.

#### Growpart

The growpart script used in this package is not from the 0.27
cloud-utils-growpart package. There are bugs in that version of growpart,
primarily a bug that doesn't respect 2TB disk partitions on MBR disks. This
means that if you had a disk that was 2.1TB, you would end up with a 0.1TB
partition instead of 2TB partition. Obviously, this is bad. The upstream
[cloud-utils 257 release](http://bazaar.launchpad.net/~cloud-utils-dev/cloud-utils/trunk/tarball/257)
fixes this bug and others while not introducing more bugs and dependencies in
further upstream releases of this script. It is therefore not recommended that
you try to use the [0.27 growpart package](http://rpmfind.net/linux/RPM/epel/6/x86_64/cloud-utils-growpart-0.27-10.el6.x86_64.html)
from the EPEL repo.

#### Dracut modules

The dracut modules are taken unmodified from the [dracut-modules-growroot](http://rpmfind.net/linux/RPM/epel/6/x86_64/dracut-modules-growroot-0.20-2.el6.noarch.html)
package in the EPEL 6 repo. The dracut module allows the partition table to be
expanded on boot before / is mounted and prevents an additional reboot.

#### The expand-root init.d script

The expand-root init.d script is derived from the
[bootstrap-vz version](https://github.com/andsens/bootstrap-vz/blob/c682dab6ec51767b6e529c1589c5630f6295953a/bootstrapvz/common/assets/init.d/expand-root)
of this script used for Debian instances. Essentially, it just calls the proper
filesystem expansion utility to live resize the filesystem on first boot. The
root partition is hard coded as /dev/sda1 in this script.

### License

The scripts in this package, unless otherwise noted, are licensed under GPLv3
from their upstream sources.
