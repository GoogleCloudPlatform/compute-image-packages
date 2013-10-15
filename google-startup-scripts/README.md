## google-startup-scrips for Google Compute Engine

Google provides a set of startup scripts that interact with the virtual machine environment. On boot, the startup script `/usr/share/google/onboot` queries the instance metadata for a user-provided startup script to run. User-provided startup scripts can be specified in the instance metadata under startup-script or, if the metadata is in a small script or a downloadable file, it can be specified via startup-script-url. You can use gcutil or the Google Compute Engine API to specify a startup script. For more information on how to use startup scripts, read the Using Start Up Scripts documentation.

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

+ Checks the value of the instance id key
  Startup scripts check the value of the instance ID at:
    
    http://metadata/computeMetadata/v1beta1/instance/id
    
  and compares it to the last instance ID the disk booted on.
+ Sets the hostname from the metadata server via DHCP exit hooks.
+ Updates gsutil authentication.
  Startup scripts run `/usr/share/google/boto/boot_setup.py` which configures and copies `/usr/share/google/boto/boto_plugins/compute_auth.py` into the boto plugin directory.
+ Provides udev rules to give friendly names to disks.
  Google Compute Engine provides `/lib/udev/rules.d/65-gce-disk-naming.rules` in our images.
+Safely formats persistent disks via `/usr/share/google/safe_format_and_mount`.
