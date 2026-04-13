#!/bin/bash

set -e 

USERNAME="${USERNAME:-dataloggerX}"
RIG_MOUNT="${RIG_MOUNT:-/mnt/raw_data}"
RIG_CONTAINER_FILE="${RIG_CONTAINER_FILE:-/home/${USERNAME}/${PROJECT_FOLDER}/rig_data_container.bin}"

echo "unmounting image"

if mount | grep -q "$RIG_MOUNT"; then  
    echo "unmounting $RIG_MOUNT"

    sync #syncs data before unmounting

    if sudo umount "$RIG_MOUNT"; then
        echo "successfully unmounted"
    else 
        echo "failed to unmount..."
        echo "check for any open files: lsof $RIG_MOUNT"
        exit 1
    fi
else
    echo "image not mounted at $RIG_MOUNT..."
fi