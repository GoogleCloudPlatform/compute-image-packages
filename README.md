## [Image Packages](https://cloud.google.com/compute/docs/images) for [Google Compute Engine](https://cloud.google.com/compute/)
This repository is the collection of packages that are installed on the standard Google Compute Engine images.

1. [Image Bundle](https://cloud.google.com/compute/docs/images#buildingimage) - Tool that creates an image file out of a disk attached to a GCE VM.
1. [Google Startup Scripts](https://cloud.google.com/compute/docs/startupscript) - Scripts and configuration files that setup a Linux-based image to work smoothly with GCE.
1. Google Daemon - A service that manages user accounts, maintains ssh login keys, syncs the system clock after migration, and syncs public endpoint IP addresses.

## Installation

### From Release Tarballs
The easiest way to install these packages into a Linux-based image is to extract each tarball to `/` (root). Image Bundle does not have a directory structure, it is recommended to it extract to `/usr/share/imagebundle`. The tarballs are available in [releases](https://github.com/GoogleCloudPlatform/compute-image-packages/releases).

Refer to [Building a Google Compute Engine Image](https://cloud.google.com/compute/docs/images) for the complete guide.

### Generate Deb/Rpm Package
You may generate a .deb or .rpm package with the script under the directory ./generate_packages. To do this:

1. Log in to your target machine.
1. Clone the repository with

        git clone https://github.com/GoogleCloudPlatform/compute-image-packages.git

2. Copy the files in directory ./generate-packages to the same directory as compute-image-packages:

        cp compute-image-packages/generate-packages/*.* .

3. Execute the script ./generate_packages.sh with root permission. It will generate both .deb and .rpm packages. You may also run the script with -r or -d parameter if you only want .rpm or .deb package.

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

1. Install gcimagebundle with

        cd compute-image-packages/gcimagebundle && sudo python setup.py install

## Source Code
This repository is structured so that each package is located in its own top-level directory. [`google-startup-scripts`](google-startup-scripts/) and [`google-daemon`](google-daemon/) are stored as the directory structure of where the files would be from root. [`image-bundle`](image-bundle/) has no directory structure.

## Contributing
Have a patch that will benefit this project? Awesome! Follow these steps to have it accepted.

1. Please sign our [Contributor License Agreement](CONTRIB.md).
1. Fork this Git repository and make your changes.
1. Run the unit tests. (gcimagebundle only)
1. Create a Pull Request
1. Incorporate review feedback to your changes.
1. Accepted!

## License
All files in this repository are under the [Apache License, Version 2.0](LICENSE) unless noted otherwise.
