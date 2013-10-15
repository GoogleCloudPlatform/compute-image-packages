## google-daemon
Google daemon runs in the background and provides the following services:

+ Creates new accounts based on the instance metadata.
+ Configures ssh to accept the accounts' public keys from the instance metadata.

Google daemon is typically located at: 

    /usr/share/google/google_daemon/manage_accounts.py

Your users can create ssh keys for accounts on a virtual machine using [gcutil](http://developers.google.com/compute/docs/gcutil "gcutil") or manually using these steps:

    # Generate the ssh keys
    $ ssh-keygen -t rsa -f ~/.ssh/google_compute_engine
    
    # Create public RSA key in OpenSSH format
    $ ssh-rsa [base-64-encoded-public-key] [comment]

In the metadata server, the SSH keys are passed to a virtual machine individually, or to the project using the `commoninstancemetadata` property:

    {
       kind: "compute#metadata",
       items: [
         "key": "sshKeys",
         "value": "<ssh-keys-value>"
      ]
    }
    
`<ssh-keys-value>` is a newline-separated list of individual authorized public ssh key records, each in the format:

    <username>:<public-ssh-key-file-contents>

For example:

    {
      "kind": "compute#project",
      "name": "project-name",
      "commonInstanceMetadata": {
      "kind": "compute#metadata",
      "items": [
      {
        "key": "sshKeys",
        "value": "user1:ssh-rsa AAAA...pIy9 user@host.domain.com\nuser2:ssh-rsa AAAA...ujOz user@host.domain.com"
      }
     ]
    }
    
For more information about the metadata server, read the [metadata server](http://developers.google.com/compute/docs/metadata "metadata server") documentation.

Inside a virtual machine, a cron job runs every minute to check if project or instance metadata was updated with the new sshKeys value, and makes sure those users exist. It also checks that the keys are in the `~$USER/.ssh/authorized_keys` file.

__Note:__ It is recommended that you use a `wait-for-change` request through the metadata server to detect updates. See [metadata server](https://developers.google.com/compute/docs/metadata#waitforchange) for more information.

Other account management software can be used instead of Google Daemon but you will have to configure the software to read user accounts from the metadata server.

