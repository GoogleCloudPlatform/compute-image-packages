## Daisy Workflows for building packages.

For more information on Daisy and how workflows work, refer to the
[Daisy documentation](https://github.com/GoogleCloudPlatform/compute-image-tools/tree/master/daisy).

# Workflow invocation

```shell
# Builds Debian packages from the development branch.
./daisy -project YOUR_PROJECT \
        -zone ZONE \
        -var:package_version=2.6.0 \
        -var:github_branch=development \
        -var:output_path=YOUR_GS_BUCKET \
        build_debian.wf.json

# Builds EL packages.
./daisy -project YOUR_PROJECT \
        -zone ZONE \
        -var:output_path=YOUR_GS_BUCKET \
        build_el.wf.json

```

# Variables

* `output_path` Specify a different GCS path to save resulting packages to.
* `github_repo` Specify a different github repo (for example a forked repo).
* `github_branch` Specify a different github branch.
