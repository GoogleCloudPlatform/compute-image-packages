## Google Startup Scripts
Google provides a set of startup scripts that interact with the virtual machine environment. On boot, the startup script `/usr/share/google/onboot` queries the instance metadata for a user-provided startup script to run. User-provided startup scripts can be specified in the instance metadata under `startup-script` or, if the metadata is in a small script or a downloadable file, it can be specified `via startup-script-url`. You can use gcutil or the [Google Compute Engine API](https://developers.google.com/compute/docs/reference/latest) to specify a startup script. 

For more information on how to use startup scripts, read the [Using Start Up Scripts documentation](https://devsite.googleplex.com/compute/docs/howtos/startupscript#storescriptremotely).

Below is an example of metadata that indicates a startup script URL and a startup script file was passed to the instance:

    { // instance
      metadata: {
        "kind": "compute#metadata",
        "items": [
        {
          "key": "startup-script-url",
          "value": "http://startup-script-url:
        }
      ]
     }
    }
    {  // instance
      metadata: {
        "kind": "compute#metadata",
        "items": [
        {
           "key": "startup-script",
           "value": "#! /bin/python\nprint ‘startup’\n"
        }
      ]
     }
    }
   
   
Google startup scripts also perform the following actions:

+ __Checks the value of the instance id key__

    Startup scripts check the value of the instance ID at:

        http://metadata/computeMetadata/v1beta1/instance/id
    
    and compares it to the last instance ID the disk booted on.
    
+ __Sets the [hostname](https://github.com/GoogleCloudPlatform/compute-image-packages/blob/master/google-startup-scripts/usr/share/google/set-hostname) from the metadata server via DHCP exit hooks.__

+ __Updates gsutil authentication.__

    Startup scripts run `/usr/share/google/boto/boot_setup.py` which configures and copies         `/usr/share/google/boto/boto_plugins/compute_auth.py` into the boto plugin directory.

+ __Provides udev rules to give friendly names to disks.__

    Google Compute Engine provides `/lib/udev/rules.d/65-gce-disk-naming.rules` in our images.

+ __Safely formats persistent disks via `/usr/share/google/safe_format_and_mount`.__
