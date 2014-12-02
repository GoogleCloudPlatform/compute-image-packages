## [Image Packages](https://cloud.google.com/compute/docs/images) for [Google Compute Engine](https://cloud.google.com/compute/)
This repository is the collection of packages that are installed on the standard Google Compute Engine images.

1. [Image Bundle](https://cloud.google.com/compute/docs/images#buildingimage) - Tool that creates an image file out of a disk attached to a GCE VM.
1. [Google Startup Scripts](https://cloud.google.com/compute/docs/startupscript) - Scripts and configuration files that setup a Linux-based image to work smoothly with GCE.
1. Google Daemon - A service that manages user accounts, maintains ssh login keys, and syncs public endpoint IP addresses.

## Installation
The easiest way to install these packages into a Linux-based image is to extract each tarball to `/` (root). Image Bundle does not have a directory structure, it is recommended to it extract to `/usr/share/imagebundle`. The tarballs are available in [releases](https://github.com/GoogleCloudPlatform/compute-image-packages/releases). 

Refer to [Building a Google Compute Engine Image](https://cloud.google.com/compute/docs/images) for the complete guide.

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
