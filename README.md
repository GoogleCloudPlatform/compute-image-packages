## Image Packages for Google Compute Engine
This repository is the collection of packages that are installed on the standard Google Compute Engine images.

1. Image Bundle - Tool that creates an image file out of a disk attached to a GCE VM.
1. Google Startup Scripts - Scripts and configuration files that setup a Linux-based image to work smoothly with GCE.
1. Google Daemon - A service that manages user accounts, maintains ssh login keys, and syncs public endpoint IP addresses.

## Installation
The easiest way to install these packages into a Linux-based image is to extract each tarball to `/` (root). Image Bundle does not have a directory structure, it is recommended to it extract to `/usr/share/imagebundle`. The tarballs are available in [releases](https://github.com/GoogleCloudPlatform/compute-image-packages/releases). 

Refer to [Building a Google Compute Engine Image](https://developers.google.com/compute/docs/building_image) for the complete guide.

## Source Code
This repository is structured so that each package is located in its own top-level directory. [`google-startup-scripts`](google-startup-scripts/) and [`google-daemon`](google-daemon/) are stored as the directory structure of where the files would be from root. [`image-bundle`](image-bundle/) has no directory structure.

## Contributing
We welcome bug fixes and enhancements. Before you can submit patches please sign our Contributor License Agreement. See CONTRIB.md for more information.

## License
All files in this repository are under the [Apache License, Version 2.0](LICENSE) unless noted otherwise.
