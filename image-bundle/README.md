##Image Bundle

Image Bundle is a python package that allows users to create an image from the current state of the running virtual machine. Image Bundle creates the image with the recommended packaging format and also allows you to run unit tests to verify that image bundle works properly on your operating system. See [Custom Images](https://developers.google.com/compute/docs/images#bundle_image) for more information.

To install:

    $ sudo python setup.py install


To build a root filesystem tar:

    $ sudo image_bundle -r /data/myimage/root -o /usr/local/google/home/${USER} \
    -k 'somekey' --loglevel=DEBUG  --log_file=/tmp/image_bundle.log

This will output the image tar in the output directory specified with -o option.

To run unit test:

    sudo python /usr/share/imagebundle/block_disk_unittest.py
    
Or, if you are in the package directory:

    $ mkdir /tmp/imagebundle
    $ cp * /tmp/imagebundle/
    $ sudo /tmp/imagebundle/block_disk_unittest.py

Note that this is copied out file by file into the default google image.

To create DEB package:

    $ python setup.py --command-packages=stdeb.command bdist_deb
    
To create RPM package:

    $ python setup.py bdist_rpm
    

