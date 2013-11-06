Image Bundle
============

Image Bundle is a python package that allows users to create an image from the current state of the running virtual machine. Image Bundle creates the image with the recommended packaging format and also allows you to run unit tests to verify that image bundle works properly on your operating system. See [Custom Images](https://developers.google.com/compute/docs/images#bundle_image) for more information.

### Installation

    $ sudo python setup.py install

### Usage

To build a root filesystem tar:

    $ sudo gcimagebundle -d /dev/sda -r / -o /tmp \
    --loglevel=DEBUG  --log_file=/tmp/image_bundle.log

This will output the image tar in the output directory specified with -o option.

For details on all the parameters use...

    $ sudo gcimagebundle --help

### Unit Tests

Image Bundle includes unit tests that should be run if you make any changes. These tests perform mount operations so root access is required.

    $ sudo python setup.py test

### Packaging

Since Image Bundle uses setuptools it can be packaged into a DEB or RPM.

Install the required dependencies:

    # For Debian based distributions
    $ sudo apt-get install python-stdeb rpm
    # For Red-Hat based distributions
    $ sudo yum install rpmbuild 

DEB package:

    $ python setup.py --command-packages=stdeb.command bdist_deb
    
RPM package:

    $ python setup.py bdist_rpm
