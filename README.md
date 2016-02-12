## [Image Packages](https://cloud.google.com/compute/docs/images) for [Google Compute Engine](https://cloud.google.com/compute/)
This repository is the collection of packages that are installed on the standard Google Compute Engine images.

1. [Google Startup Scripts](https://cloud.google.com/compute/docs/startupscript) - Scripts and configuration files that setup a Linux-based image to work smoothly with GCE.
1. Google Daemon - A service that manages user accounts, maintains ssh login keys, syncs the system clock after migration, and syncs public endpoint IP addresses.
1. Disk Expand - Scripts to expand the root partition on GCE VM's for CentOS 6 and RHEL 6 images.

Note: gcimagebundle is deprecated and is provided here as is with no further
support or maintenance. See [replacement instructions](https://cloud.google.com/compute/docs/creating-custom-image#export_an_image_to_google_cloud_storage).

## Installation

### From Release Tarballs
The easiest way to install these packages into a Linux-based image is to extract each tarball to `/` (root). Image Bundle does not have a directory structure, it is recommended to it extract to `/usr/share/imagebundle`. The tarballs are available in [releases](https://github.com/GoogleCloudPlatform/compute-image-packages/releases). 

Refer to [Building a Google Compute Engine Image](https://cloud.google.com/compute/docs/images) for the complete guide.

### From Source Repository
Occasionally you may want to install the latest commits to the [repository](https://github.com/GoogleCloudPlatform/compute-image-packages/) even if they have not been released. This is not recommended unless there is a change that you specifically need and cannot wait for. To do this:

1. Log in to your target machine.
1. Clone the repository with

        git clone https://github.com/GoogleCloudPlatform/compute-image-packages.git

1. Copy the google-daemon and google-startup-scripts files to your root directory with

        sudo cp -R compute-image-packages/{google-daemon/{etc,usr},google-startup-scripts/{etc,usr,lib}} /

1. Configure the packages to run on startup with (Debian)

        sudo update-rc.d google-startup-scripts defaults && sudo update-rc.d google-accounts-manager defaults && sudo update-rc.d google-address-manager defaults && sudo update-rc.d google-clock-sync-manager defaults

   or (Redhat)

        sudo chkconfig --add google-startup-scripts && sudo chkconfig --add google-accounts-manager && sudo chkconfig --add google-address-manager && sudo chkconfig --add google-clock-sync-manager

1. Either restart so the packages run or start them with (Debian and Redhat)

        sudo service google-accounts-manager restart && sudo service google-address-manager restart && sudo service google-clock-sync-manager restart

## Source Code
This repository is structured so that each package is located in its own top-level directory. [`google-startup-scripts`](google-startup-scripts/) and [`google-daemon`](google-daemon/) are stored as the directory structure of where the files would be from root.

## Contributing
Have a patch that will benefit this project? Awesome! Follow these steps to have it accepted.

1. Please sign our [Contributor License Agreement](CONTRIB.md).
1. Fork this Git repository and make your changes.
1. Create a Pull Request
1. Incorporate review feedback to your changes.
1. Accepted!

## License
All files in this repository are under the [Apache License, Version 2.0](LICENSE) unless noted otherwise.
