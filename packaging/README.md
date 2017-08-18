## Daisy Workflows for building packages.

For more information on Daisy and how workflows work, refer to the
[Daisy documentation](https://github.com/GoogleCloudPlatform/compute-image-tools/tree/master/daisy).

# Workflow invocation

```shell
# Builds Debian packages.
./daisy -project YOUR_PROJECT \
        -zone ZONE \
        -gcs_path YOUR_GCS_PATCH \
        -variables package_version=2.6.0 \
        build_debian.wf.json

# Builds EL6 packages.
./daisy -project YOUR_PROJECT \
        -zone ZONE \
        -gcs_path YOUR_GCS_PATCH \
        -variables package_version=2.6.0 \
        build_el6.wf.json

# Builds EL7 packages.
./daisy -project YOUR_PROJECT \
        -zone ZONE \
        -gcs_path YOUR_GCS_PATCH \
        -variables package_version=2.6.0 \
        build_el7.wf.json
```

# Variables

* output_path: Specify a different GCS path to save resulting packages to.
* github_repo: Specify a different github repo (for example a forked repo).
* github_branch: Specify a different github branch.
* package_version: The version of the package- this version has to match the version
  of the python setup.py files, spec files, and Debian changelog.
