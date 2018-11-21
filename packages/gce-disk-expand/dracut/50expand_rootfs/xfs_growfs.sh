#!/bin/sh

main() {
        if [ -z "$expand_xfs" ]; then
            return
        fi
        if ! command -v xfs_growfs >/dev/null; then
            echo "XFS resize requested, but xfs_growfs not installed"
            return
        fi
	if xfs_growfs -d -n /sysroot; then
	   echo "Resizing XFS filesystem"
	   if ! out=$(xfs_growfs -d /sysroot); then
	       echo "Failed to resize: ${out}"
	       return
	   fi
	fi
}

main
