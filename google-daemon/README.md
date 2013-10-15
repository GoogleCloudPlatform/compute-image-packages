## google-daemon package for Google Compute Engine
The google-daemon package creates new accounts and configures ssh to accept public keys. Google daemon runs in the background and provides the following services:

+ Creates new accounts based on the instance metadata.
+ Configures ssh to accept the accounts' public keys from the instance metadata.

Google daemon is typically located at: 
    /usr/share/google/google_daemon/manage_accounts.py

Your users can create ssh keys for accounts on a virtual machine using [gcutil](http://developers.google.com/compute/docs/gcutil "gcutil") or manually using these steps:

    # Generate the ssh keys
    $ ssh-keygen -t rsa -f ~/.ssh/google_compute_engine
    
    # Create public RSA key in OpenSSH format
    $ ssh-rsa [base-64-encoded-public-key] [comment]
