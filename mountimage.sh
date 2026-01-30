#!/bin/bash


set -e #exit on an error

USERNAME="${USERNAME:-datalogger364}"
PROJECT_FOLDER="${PROJECT_FOLDER:-pi-sharepoint-upload}"
RIG_MOUNT="${RIG_MOUNT:-/mnt/raw_data}"
RIG_CONTAINER_FILE="${RIG_CONTAINER_FILE:-/home/datalogger364/pi-sharepoint-upload/rig_data_container.bin}"

echo "Config Loads..."
echo "  User: $USERNAME"
echo "  Project Folder: $PROJECT_FOLDER"
echo "  Rig Mount: $RIG_MOUNT"
echo "  Container File: $RIG_CONTAINER_FILE"

#turn off gadget mode
/home/$USERNAME/$PROJECT_FOLDER/toggle_gadget.sh stop

#verify that the device exists
if [ ! -f "$RIG_CONTAINER_FILE" ]; then
    echo "ERROR: .bin container file not found. two possible fixes"
    echo "Run setup first: sudo dd if=/dev/zero of=/rig_data_container.bin bs=1M count=1024"
    echo "Then: sudo mkdosfs /rig_data_container.bin -F 32 -I"
    exit 1
fi 

#unmount if already mounted
if mount | grep -q "$RIG_MOUNT"; then
    echo "image already mounted at $RIG_MOUNT"
    sudo umount "$RIG_MOUNT" 2>/dev/null || true
fi

#create mount point 
echo "creating mount point: $RIG_MOUNT"

sudo mkdir -p "$RIG_MOUNT"
sudo chown "$USERNAME:$USERNAME" "$RIG_MOUNT"

#mounting device
echo "Mounting image to $RIG_MOUNT"

if sudo mount -o loop,uid=$USERNAME,gid=$USERNAME "$RIG_CONTAINER_FILE" "$RIG_MOUNT"; then
    echo "mount successful"
    # Show contents
    echo ""
    echo "Contents of $RIG_MOUNT:"
    ls -la "$RIG_MOUNT/"
    
else
    echo "mount failed"
    exit 1
fi