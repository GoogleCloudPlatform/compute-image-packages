#!/bin/bash
#
#
# Embedds a kernel into disk or image if it doesn't have one.
# Arguments:
#   project_name       : Name of the project in which the resource lives
#   Disk/image         : Disk if a disk needs to be updated, or else image
#   resource_name      : Name of the disk/resource that needs to be updated
#   temp_instance_name : Name of the instance that can be created by the tool to update the disk/image
#   temp_

project_name=
source_image_name=
destination_image_name=
source_disk_name=
source_disk_zone=
temp_instance_name=
temp_instance_zone=
do_not_delete_instance=false
tmp_file=
machine_type=n1-standard-1
gcg_kernel=projects/google/global/kernels/gce-no-conn-track-v20130813
gcutil=/google/data/ro/projects/cloud/cluster/gcutil

# Enable exit on error
set -e

function cleanup () {
  if ! $do_not_delete_instance; then
     echo 'skipping delete'
     return
  fi
  if [ -n $temp_instance_zone ];
    then
      # Delete the instance
      $gcutil --project=$project_name deleteinstance $temp_instance_name --zone=$temp_instance_zone --nodelete_boot_pd --force
    temp_instance_zone=''
  fi
  if [ -n $tmp_file ];
    then
      rm $tmp_file
  fi
}

function die () {
  echo "$1" >&2
  exit 1
}

function runRemoteScript () {
  cat $tmp_file | $gcutil --project=$project_name ssh $temp_instance_name 'bash -s'
}

function embeddKernelOnDisk() {
  # Check if there is a disk that needs to be migrated
  if [ -z $source_disk_name ];
    then
       echo 'No source disk'
       return
  fi
  # Verify we have a zone for the disk
  if [ -z $source_disk_zone ];
    then
       echo 'Please specify the zone for the disk'
       die
  fi

  temp_instance_zone=$source_disk_zone
  # Create an instance in the same zone with the disk as the boot disk
  $gcutil --project=$project_name --service_version=v1beta16 addinstance $temp_instance_name --disk=$source_disk_name,boot --zone=$temp_instance_zone --wait_until_running --machine_type=$machine_type --kernel=$gcg_kernel

  # sleep for 10 seconds to ensure the instance is sshable
  sleep 10s

  # Run the script to embedd the kernel
  runRemoteScript $embedd_kernel_script

  
  # Delete the instance
  cleanup

}

# List of options for gce subcommand
help="embedd-kernel
This script embedds a kernel into an image or disk

Options (defaults in ${txtbld}bold${txtdef}):

${txtund}Bootstrapping${txtdef}
    --project-name 	NAME     	Name of the project (${txtbld}${arch}${txtdef})
    --source-image-name	SOURCE-Image    Source image in which to embedd the kernel (${txtbld}${arch}${txtdef})
    --dest-image-name   DEST-IMAGE      Destination image name (${txtbld}${arch}${txtdef})
    --source-disk-name 	SOURCE-DISK     Source disk in which to embedd the kernel (${txtbld}${arch}${txtdef})
    --source-disk-zone	SOURCE-DISK-ZONE Zone of source disk (${txtbld}${arch}${txtdef})
    --temp-instance-name TEMP-INSTANCE-NAME The name for the instance that the tool will create to embedd the kernel (${txtbld}${arch}${txtdef})
    --do-not-delete-instance [true|false] True if instance should not be deleted. defaults to true (${txtbld}${arch}${txtdef})

${txtund}Other options${txtdef}
    --debug                       Print debugging information
    --help                        Prints this help message
"

# Run through the parameters and save them to variables.
while [ $# -gt 0 ]; do
        case $1 in
                --project-name)         project_name=$2;               shift 2 ;;
                --source-image-name)             source_image_name=$2;                   shift 2 ;;
                --dest-image-name)           destination_image_name=$2;                 shift 2 ;;
                --source-disk-name)          source_disk_name=$2;                shift 2 ;;
                --source-disk-zone)                 source_disk_zone=$2;                shift 2 ;;
                --temp-instance-name)          temp_instance_name=$2;                shift 2 ;;
                --do-not-delete-instance)          do_not_delete_instance=$2;                shift 2 ;;
                --debug)                set -x;                        shift   ;;
                -h|--help)              printf -- "$help";             exit 0  ;;
                *)             die "Unrecognized option: $1" \
    "Type '$0 --help' to see a list of possible options"; ;;
        esac
done

echo $project_name $source_image_name $destination_image_name $source_disk_name $source_disk_zone $temp_instance_name

tmp_file=/tmp/$RANDOM.bash
cat >> $tmp_file << EOF
yes | sudo apt-get install linux-image-amd64
yes | sudo apt-get install grub-pc
EOF


# Ensure cleanup gets called on error
trap cleanup ERR EXIT

# Embedd kernel in the disk
embeddKernelOnDisk

# Embedd kernel in the image
