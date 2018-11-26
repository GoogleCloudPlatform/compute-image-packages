#!/bin/bash

# TODO: license and description
# takes rhel6 dracut and modifies it for rhel7

mv src/usr/share src/usr/lib
pushd src/usr/lib/dracut/modules.d/50expand_rootfs

cat >module-setup.sh <<EOF
#!/bin/bash

check() {
`grep -iv ^'#!' check`
}

install() {
`grep -iv ^'#!' install`
}
EOF

rm install check
popd
