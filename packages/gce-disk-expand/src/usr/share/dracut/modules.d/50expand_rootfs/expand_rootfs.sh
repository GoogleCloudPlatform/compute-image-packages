#!/bin/sh

expand_xfs=""  # global to message next script

# Contains dracut-specific logic for detecting disk, then calls appropriate
# library functions.
main() {
        local disk="" partnum="" fs_type="" rootdev=""

        # Remove 'block:' prefix and find the root device
        if ! rootdev=$(readlink -f "${root#block:}") || [ -z "${rootdev}" ]; then
                echo "unable to find root device"
                return
        fi

        # Wait for any of the initial udev events to finish otherwise growpart
        # might fail
        udevsettle

        if ! out=$(get_partition "$rootdev"); then
          echo "Failed to detect disk and partition info: ${out}"
          return
        fi

        disk=${out%:*}
        partnum=${out#*:}

        if ! parted_needresize "$disk" "$partnum"; then
            echo "Disk does not need resizing"
            return
        fi

        echo "Resizing disk ${rootdev}"

        if ! out=$(parted_fix_gpt); then
            echo "$out"
            return
        fi

        # TODO: check all error conditions and echos
        # TODO: move split into resize ? (but both resize and check need split)
        # TODO: variable names and indentation
        # TODO: split fs resize, run afterward
        if parted --help|grep -q 'resizepart'; then
            if ! out=$(parted_resizepart "$disk" "$partnum"); then
                echo "Failed to resize partition: ${out}"
                return
            fi
        else
            echo "parted doesn't support 'resizepart' command, trying rm&&mkpart"
            if ! out=$(parted_resize_mkpart "$disk" "$partnum"); then
                echo "Failed to resize partition: ${out}"
                return
            fi
        fi

        udevsettle

        if ! out=$(resize_filesystem "$rootdev"); then
            echo "Failed to resize filesystem: ${out}"
            return
        fi
}

. /lib/expandfs-lib.sh
echo DEBUG DEBUG
main
