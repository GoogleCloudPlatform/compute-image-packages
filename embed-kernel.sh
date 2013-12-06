#!/bin/bash
#
#
# embeds a kernel into disk or image if it doesn't have one.
# Example usage
# Migrating a disk named mydisk in us-central1-a zone in project named myprojec
#    embed-kernel.sh --project-name myproject --disk-name mydisk --disk-zone us-central1-a \
#        --temp-instance-name temp --resource-type Disk
#
# Migrating an imag named myimage in project named myprojec
#    embed-kernel.sh --project-name myproject --image-name myimage \
#        --temp-instance-name temp --resource-type Image

project_name=
resource_type=
source_image_name=
source_disk_name=
source_disk_zone=
temp_instance_name=
temp_instance_zone=
do_not_delete_instance=false
skip_instance_creation=false
embed_script=
debian_embed_script=
centos_embed_script=
run_gcimagebundle_script=
tarfile_location=
no_delete_boot_pd=
cleanup_required=true
machine_type=n1-standard-8
gcg_kernel=projects/google/global/kernels/gce-no-conn-track-v20130813
gcutil=gcutil # replace with path to gcutil

# Enable exit on error
set -e

function deleteinstance () {
  # Delete the instance
  $gcutil --project=$project_name deleteinstance $temp_instance_name --zone=$temp_instance_zone $1 --force
}

function cleanup () {
  if $do_not_delete_instance; then
     echo 'skipping delete'
     return
  fi
  if $cleanup_required;
    then
      if [ $resource_type == 'Image' ];
        then
          # Delete the instance and the disk attached to it
          deleteinstance '--delete_boot_pd'
      fi
      if [ $resource_type == 'Disk' ];
        then
          # Delete the instance but not the disk
          deleteinstance '--nodelete_boot_pd'
      fi
  fi
  if [ -n $debian_embed_script ];
    then
      rm $debian_embed_script
  fi
  if [ -n $centos_embed_script ];
    then
      rm $centos_embed_script
  fi
  if [ -n $run_gcimagebundle_script ];
    then
      rm $run_gcimagebundle_script
  fi
  if [ -n $tarfile_location ];
    then
      echo 'Image tar archive with kernel located at '$tarfile_location
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

function pushScript() {
  $gcutil --project=$project_name push $temp_instance_name $1 $1
  runRemoteScript 'chmod +x '$1
}

function embedKernel() {
  # sleep for 30 seconds to ensure the instance is sshable
  if ! $skip_instance_creation;
    then
      echo 'waiting for instance to become sshable'
      sleep 30s
  fi

debian_embed_script=/tmp/debian-embed-kernel.bash
cat > $debian_embed_script << EOF
set -x
export PATH=$PATH:/usr/sbin
echo 'y' | sudo apt-get install linux-image-amd64
echo 'y' | sudo apt-get install debconf-utils
echo 'grub-pc grub-pc/install_devices multiselect /dev/sda' |debconf-set-selections
echo 'y' | sudo apt-get install grub-pc
curl -L --remote-name-all https://github.com/GoogleCloudPlatform/compute-image-packages/releases/download/1.1.0.1/google-startup-scripts_1.1.0-4_all.deb https://github.com/GoogleCloudPlatform/compute-image-packages/releases/download/1.1.0.1/google-compute-daemon_1.1.0-4_all.deb https://github.com/GoogleCloudPlatform/compute-image-packages/releases/download/1.1.0.1/python-gcimagebundle_1.1.0-3_all.deb
sudo dpkg -i google-startup-scripts_1.1.0-4_all.deb google-compute-daemon_1.1.0-4_all.deb python-gcimagebundle_1.1.0-3_all.deb
sudo apt-get -f -y install
sudo shutdown -h now
EOF

centos_embed_script=/tmp/centos-embed-kernel.bash
cat > $centos_embed_script << 'EOF'
set -x
echo 'y' | sudo yum install kernel-xen
UUID=`sudo /sbin/tune2fs -l /dev/sda1 | grep UUID | awk '{ print $3 }'`
echo $UUID
if [ -z $UUID ];
  then
     echo 'unable to determine UUID'
     exit 1
fi
INITRAM=`ls /boot/init* | grep init | awk '{ print $1 }'`
echo $INITRAM
if [ -z $INITRAM ];
  then
     echo 'unable to determine INITRAM'
     exit 1
fi
KERNEL=`ls /boot/vmlinuz* | grep vmlinuz | awk '{ print $1 }'`
echo $KERNEL
if [ -z $KERNEL ];
  then
     echo 'unable to determine KERNEL'
     exit 1
fi
sudo mkdir /boot/grub
sudo bash -c "echo \"default
timeout=0

title CentOS
    root (hd0,0)
    kernel $KERNEL ro root=UUID=$UUID noquiet earlyprintk=ttyS0 loglevel=8
    initrd $INITRAM\" > /boot/grub/grub.conf"
echo 'y' | sudo yum install grub
sudo /sbin/grub-install /dev/sda1
sudo bash -c "echo \"
find /boot/grub/stage1
root (hd0,0)
setup (hd0)
quit\" | /sbin/grub"

echo 'y' | sudo yum install https://github.com/GoogleCloudPlatform/compute-image-packages/releases/download/1.1.0.1/google-compute-daemon-1.1.0-4.noarch.rpm https://github.com/GoogleCloudPlatform/compute-image-packages/releases/download/1.1.0.1/google-startup-scripts-1.1.0-4.noarch.rpm https://github.com/GoogleCloudPlatform/compute-image-packages/releases/download/1.1.0.1/gcimagebundle-1.1.0-3.noarch.rpm

sudo ln -s /dev/null /etc/udev/rules.d/75-persistent-net-generator.rules
sudo chattr -i /etc/udev/rules.d/70-persistent-net.rules
sudo rm -f /dev/null /etc/udev/rules.d/70-persistent-net.rules
sudo mkdir /var/lock/subsys
sudo chmod 755 /var/lock/subsys
EOF

embed_script=/tmp/embed$RANDOM.bash
cat > $embed_script << 'EOF'
set -x
RELEASE_FILE=`ls /etc/*-release`
echo $RELEASE_FILE
CENTOS=`cat $RELEASE_FILE |grep CentOS`
WHEEZY=`cat $RELEASE_FILE |grep wheezy`
echo $CENTOS
echo $WHEEZY
if [ -n "${CENTOS}" ] && [ -n "${WHEEZY}" ];
  then
    echo 'Error in detecting OS'
    exit 1
fi
if [ -z "${CENTOS}" ] && [ -z "${WHEEZY}" ];
  then
    echo 'Only CentOS 6 and Debian 7 Wheezy are supported'
    exit 1
fi

if [ -n "${CENTOS}" ];
  then
    sh /tmp/centos-embed-kernel.bash
fi
if [ -n "${WHEEZY}" ];
  then
    sh /tmp/debian-embed-kernel.bash
fi
EOF


  # push the scripts to the instance
  pushScript $embed_script
  pushScript $centos_embed_script
  pushScript $debian_embed_script

  # Run the script to embed the kernel
  echo 'embeding Kernel'
  runRemoteScript 'sudo '$embed_script
}

function rungcImageBundle() {

  tarfile_location=/tmp/imagefile$RANDOM.tar.gz
  run_gcimagebundle_script=/tmp/rungcimagebundle$RANDOM.bash
  cat >> $run_gcimagebundle_script << 'EOF'
set -x
export PATH=$PATH:/sbin
TARFILE=`sudo gcimagebundle -d /dev/sda -o /tmp |grep tar.gz| awk '{ print $5 }'`
echo $TARFILE
cp $TARFILE /tmp/imagewithkernel.tar.gz
EOF

  # push the script to the instance and run it
  echo 'Running gcimagebundle'
  pushScript $run_gcimagebundle_script
  runRemoteScript 'sudo '$run_gcimagebundle_script

  # download the image file
  $gcutil --project=$project_name pull $temp_instance_name /tmp/imagewithkernel.tar.gz $tarfile_location

  echo 'Image file located at '$tarfile_location
}

function addInstanceWithV1 () {
  $gcutil --project=$project_name --service_version=v1 addinstance $temp_instance_name --disk=$1,boot --zone=$temp_instance_zone --wait_until_running --machine_type=$machine_type

  # Wait for the instance to become sshable
  echo 'waiting for instance to become sshable'
  sleep 120s
}

function embedKernelOnImage() {
  # Check if the image has been specified or not
  if [ -z $source_image_name ];
    then
       echo 'No image specified'
       return
  fi

  if ! $skip_instance_creation;
    then
      echo 'Creating instance with v1beta16'
      temp_instance_zone='us-central1-a'
      # Create an instance with the image
      $gcutil --project=$project_name --service_version=v1beta16 addinstance $temp_instance_name --image=$source_image_name --zone=$temp_instance_zone --wait_until_running --machine_type=$machine_type --kernel=$gcg_kernel --persistent_boot_disk

  fi

  embedKernel

  # Delete the instance but keep the PD
  echo 'Deleting instance which was created v1beta16'
  deleteinstance '--nodelete_boot_pd'

  # Create the instance again with the disk as the boot disk using v1
  echo 'Adding instance with v1'
  addInstanceWithV1 $temp_instance_name

  # Run gcimagebundle to create an image. This method will create the tar.gz
  # file, download it to local /tmp, and then print out the location.
  rungcImageBundle
  
  # Delete the instance and the pd since it was created by us
  deleteinstance '--delete_boot_pd'

  cleanup_required=false
}

function embedKernelOnDisk() {
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

  # Create a snapshot before we update the disk
  echo 'Creating snapshot '$source_disk_name-migrate-backup
  $gcutil --project=$project_name addsnapshot $source_disk_name-migrate-backup --source_disk=$source_disk_name

  # Create an instance in the same zone with the disk as the boot disk
  echo 'Creating instance using v1beta16'
  $gcutil --project=$project_name --service_version=v1beta16 addinstance $temp_instance_name --disk=$source_disk_name,boot --zone=$temp_instance_zone --wait_until_running --machine_type=$machine_type --kernel=$gcg_kernel

  embedKernel
  
  # Delete the temporary instance
  echo 'Deleting instance which was created v1beta16'
  deleteinstance '--nodelete_boot_pd'

  # Re-create the instance using the kernel on the disk
  echo 'Adding instance with v1'
  addInstanceWithV1 $source_disk_name

  # Verify that the instance is sshable
  echo 'Verifying kernel on the instance'
  runRemoteScript '/bin/uname -a'

  # Delete the instance
  deleteinstance '--nodelete_boot_pd'

  echo 'Kernel has been embeded in the disk -'$source_disk_name

  cleanup_required=false
}

# List of options for gce subcommand
help="embed-kernel
This script embeds a kernel into an image or disk

Options (defaults in ${txtbld}bold${txtdef}):

${txtund}Bootstrapping${txtdef}
    --project-name         NAME             Name of the project (${txtbld}${arch}${txtdef})
    --resource-type [Image|Disk]  Type of resource to update (${txtbld}${arch}${txtdef})
    --image-name        SOURCE-Image    Source image in which to embed the kernel (${txtbld}${arch}${txtdef})
    --disk-name         SOURCE-DISK     Source disk in which to embed the kernel (${txtbld}${arch}${txtdef})
    --disk-zone        SOURCE-DISK-ZONE Zone of source disk (${txtbld}${arch}${txtdef})
    --temp-instance-name TEMP-INSTANCE-NAME The name for the instance that the tool will create to embed the kernel (${txtbld}${arch}${txtdef})

${txtund}Other options${txtdef}
    --debug                       Print debugging information
    --help                        Prints this help message

${txtund}Examples ${txtdef}
Migrating a disk named mydisk in us-central1-a zone in project named myprojec
    embed-kernel.sh --project-name myproject --disk-name mydisk --disk-zone us-central1-a --temp-instance-name temp --resource-type Disk

Migrating an imag named myimage in project named myprojec
    embed-kernel.sh --project-name myproject --image-name myimage --temp-instance-name temp --resource-type Image

"

# Run through the parameters and save them to variables.
while [ $# -gt 0 ]; do
        case $1 in
                --project-name)         project_name=$2;               shift 2 ;;
                --resource-type)             resource_type=$2;                   shift 2 ;;
                --image-name)             source_image_name=$2;                   shift 2 ;;
                --disk-name)          source_disk_name=$2;                shift 2 ;;
                --disk-zone)                 source_disk_zone=$2;                shift 2 ;;
                --temp-instance-name)          temp_instance_name=$2;                shift 2 ;;
                --do-not-delete-instance)          do_not_delete_instance=$2;                shift 2 ;;
                --skip-instance-creation)          skip_instance_creation=$2;                shift 2 ;;
                --debug)                set -x;                        shift   ;;
                -h|--help)              printf -- "$help";             exit 0  ;;
                *)             die "Unrecognized option: $1" \
    "Type '$0 --help' to see a list of possible options"; ;;
        esac
done

if [ -z $resource_type ];
  then
    die 'Must specify the resource-type. Run embed-kernel --help to get help'
fi

if [ $resource_type != 'Image' ];
  then
    if [ $resource_type != 'Disk' ];
      then
        die 'resource-type must be one of Image or Disk. Run embed-kernel --help to get help'
    fi
fi

# Ensure cleanup gets called on error
trap cleanup ERR EXIT

if [ $resource_type == 'Image' ]
  then
    # embed kernel in the image
    embedKernelOnImage    
    exit 0
fi

if [ $resource_type == 'Disk' ]
  then
    # embed kernel in the disk
    embedKernelOnDisk
    exit 0
fi

die 'Error'
