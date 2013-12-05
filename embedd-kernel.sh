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
skip_instance_creation=false
debian_embedd_script=
centos_embedd_script=
debian_embedd_script_filename=
centos_embedd_script_filename=
machine_type=n1-standard-1
gcg_kernel=projects/google/global/kernels/gce-no-conn-track-v20130813
gcutil=/google/data/ro/projects/cloud/cluster/gcutil

# Enable exit on error
set -e

function deleteinstance () {
  no_delete_bood_pd = $1
  if [ -n $temp_instance_zone ];
    then
      # Delete the instance
      $gcutil --project=$project_name deleteinstance $temp_instance_name --zone=$temp_instance_zone $nodelete_boot_pd --force
    temp_instance_zone=''
  fi
}

function cleanup () {
  if $do_not_delete_instance; then
     echo 'skipping delete'
     return
  fi
  deleteinstance $1
  if [ -n $debian_embedd_script ];
    then
      rm $debian_embedd_script
  fi
  if [ -n $centos_embedd_script ];
    then
      rm $centos_embedd_script
  fi
}

function die () {
  echo "$1" >&2
  exit 1
}

function runRemoteScript () {
  echo 'running'
  echo $1
  echo $1 | $gcutil --project=$project_name ssh $temp_instance_name 'bash -s'
}

function embeddKernel() {
  # sleep for 10 seconds to ensure the instance is sshable
  if ! $skip_instance_creation;
    then
      echo 'sleeping'
      sleep 20s
  fi

  # push the script to the instance
  $gcutil --project=$project_name push $temp_instance_name $centos_embedd_script /home/$USER/
  export centos_embedd_script=$centos_embedd_script
  # Run the script to embedd the kernel
  runRemoteScript 'chmod +x /home/'$USER'/'$centos_embedd_script_filename
  #runRemoteScript 'sudo /home/'$USER'/'$centos_embedd_script_filename

}

function embeddKernelOnImage() {
  # Check if the image has been specified or not
  if [ -z $source_image_name ];
    then
       echo 'No image specified'
       return
  fi

  if ! $skip_instance_creation;
    then
      echo 'Creating instance'
      temp_instance_zone='us-central1-a'
      # Create an instance with the image
      $gcutil --project=$project_name --service_version=v1beta16 addinstance $temp_instance_name --image=$source_image_name --zone=$temp_instance_zone --wait_until_running --machine_type=$machine_type --kernel=$gcg_kernel --persistent_boot_disk

  fi

  embeddKernel
  
  # Delete the instance but keep the PD
  deleteinstance '--nodelete_boot_pd'

  # Create the instance again with the disk as the boot disk using v1
  $gcutil --project=$project_name --service_version=v1b addinstance $temp_instance_name --disk=$temp_instance_name,boot --zone=$temp_instance_zone --wait_until_running --machine_type=$machine_type --persistent_boot_disk

  # Run gcimagebundle to create an image
  runRemoteScript 'sudo gcimagebundle -d /dev/sda -o /tmp |grep tar'
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

  embeddKernel
  
  # Delete the instance
  cleanup '--nodelete_boot_pd'
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
                --skip-instance-creation)          skip_instance_creation=$2;                shift 2 ;;
                --debug)                set -x;                        shift   ;;
                -h|--help)              printf -- "$help";             exit 0  ;;
                *)             die "Unrecognized option: $1" \
    "Type '$0 --help' to see a list of possible options"; ;;
        esac
done

echo $project_name $source_image_name $destination_image_name $source_disk_name $source_disk_zone $temp_instance_name

debian_embedd_script_filename=debian$RANDOM.bash
debian_embedd_script=/tmp/$debian_embedd_script_filename
cat >> $debian_embedd_script << EOF
sudo apt-get install linux-image-amd64
sudo apt-get install grub-pc
EOF

centos_embedd_script_filename=centos$RANDOM.bash
centos_embedd_script=/tmp/$centos_embedd_script_filename
cat >> $centos_embedd_script << 'EOF'
echo 'y' | sudo yum install kernel-xen
UUID=`sudo tune2fs -l /dev/sda1 | grep UUID | awk '{ print $3 }'`
echo $UUID
INITRAM=`ls /boot/init* | grep init | awk '{ print $1 }'`
echo $INITRAM
KERNEL=`ls /boot/vmlinuz* | grep vmlinuz | awk '{ print $1 }'`
echo $KERNEL
sudo mkdir /boot/grub
sudo bash -c "echo \"default
timeout=2

title CentOS
    root (hd0,0)
    kernel $KERNEL ro root=UUID=$UUID noquiet earlyprintk=ttyS0 loglevel=8
    initrd $INITRAM\" > /boot/grub/grub.conf"
echo 'y' | sudo yum install grub
sudo grub-install /dev/sda1
sudo bash -c "echo \"
find /boot/grub/stage1
root (hd0,0)
setup (hd0)
quit\" | grub"

echo 'y' | sudo yum install https://github.com/GoogleCloudPlatform/compute-image-packages/releases/download/1.1.0/google-compute-daemon-1.1.0-3.noarch.rpm https://github.com/GoogleCloudPlatform/compute-image-packages/releases/download/1.1.0.1/google-startup-scripts-1.1.0-4.noarch.rpm https://github.com/GoogleCloudPlatform/compute-image-packages/releases/download/1.1.0.1/gcimagebundle-1.1.0-3.noarch.rpm

sudo ln -s /dev/null /etc/udev/rules.d/75-persistent-net-generator.rules
sudo chattr -i /etc/udev/rules.d/70-persistent-net.rules
sudo rm -f /dev/null /etc/udev/rules.d/70-persistent-net.rules
sudo mkdir /var/lock/subsys
sudo chmod 755 /var/lock/subsys
sudo /etc/init.d/sshd restart
sudo shutdown -h now
EOF


# Ensure cleanup gets called on error
trap cleanup ERR EXIT

# Embedd kernel in the disk
embeddKernelOnDisk

# Embedd kernel in the image
embeddKernelOnImage
