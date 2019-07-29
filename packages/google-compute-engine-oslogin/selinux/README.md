## SELinux policy module for OS Login

This module adds specific policy updates which enable OS Login features to
function on SELinux-enabled systems (currently default on GCE RHEL6/7 images).

It primarily enables `SSHD(8)` to make network calls to the metadata server to
verify OS Login users, and to create per-user `SUDOERS(5)` files in
`/var/google-sudoers.d`

### Building the module

The provided Makefile compiles type enforcement and file context files into a
binary SELinux policy module. It must be compiled on the oldest version of the
destination OS you intend to support, as binary module versions are not
backwards compatible. Therefore, this Makefile is not run as part of the normal
packaging process but is done 'by hand', only when changes are made to the
policy.
