#!/bin/sh

# Environment variables that this script relies upon:
# - root

_info() {
        echo "growroot: $*"
}

_warning() {
        echo "growroot Warning: $*" >&2
}

# This will drop us into an emergency shell
_fatal() {
        echo "growroot Fatal: $*" >&2
        exit 1
}

_growroot() {
        # Remove 'block:' prefix and find the root device
        rootdev=$(readlink -f "${root#block:}")
        if [ -z "${rootdev}" ] ; then
                _warning "unable to find root device"
                return
        fi

        # If the basename of the root device (ie 'xvda1', 'sda1', 'vda') exists
        # in /sys/block/ then it is a block device, not a partition
        if [ -e "/sys/block/${rootdev##*/}" ] ; then
                _info "${rootdev} is not a partition"
                return
        fi

        # Check if the root device is a partition (name ends with a digit)
        if [ "${rootdev%[0-9]}" = "${rootdev}" ] ; then
                _warning "${rootdev} is not a partition"
                return
        fi

        # Remove all numbers from the end of rootdev to get the rootdisk and
        # partition number
        rootdisk=${rootdev}
        while [ "${rootdisk%[0-9]}" != "${rootdisk}" ] ; do
                rootdisk=${rootdisk%[0-9]}
        done
        partnum=${rootdev#${rootdisk}}

        # Check if we need to strip a trailing 'p' from the rootdisk name (for
        # device names like /dev/mmcblk0p)
        tmp=${rootdisk%[0-9]p}
        if [ "${#tmp}" != "${#rootdisk}" ] ; then
                rootdisk=${rootdisk%p}
        fi

        # Do a growpart dry run and exit if it fails or doesn't have anything
        # to do
        if ! out=$(growpart --dry-run "${rootdisk}" "${partnum}") ; then
                _info "${out}"
                return
        fi

        # Wait for any of the initial udev events to finish otherwise growpart
        # might fail
        udevadm settle --timeout=30

        # Resize the root partition
        if out=$(growpart --update off "${rootdisk}" "${partnum}" 2>&1) ; then
                _info "${out}"
        else
                _warning "${out}"
                _warning "growpart failed"
        fi

        # Wait for the partition re-read events to complete so that the root
        # partition is available for mounting
        udevadm settle --timeout=30

        # Add the root partition if it didn't come back on its own
        if ! [ -e "${rootdev}" ] ; then
                partx --add --nr "${partnum}" "${rootdisk}" || \
                        _warning "failed to add root device ${rootdev}"
                udevadm settle --timeout=30
        fi
}

_growroot

# vi: ts=4 noexpandtab
