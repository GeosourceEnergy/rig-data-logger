#!/bin/bash

set -e 

USERNAME="${USERNAME:-datalogger}"
USB_FOLDER_NAME="${USB_FOLDER_NAME:-usb_storage}"
USB_MOUNT="/media/$USERNAME/$USB_ID"

echo "unmounting USB"

if mount | grep -q "$USB_MOUNT"; then  
    echo "unmounting $USB_MOUNT"

    sync #syncs data to USB

    if sudo umount "$USB_MOUNT"; then
        echo "successfully unmounted"

        #remove mount directory 
        sudo rmdir "$USB_MOUNT" 2>/dev/null && echo "cleaned up mount dir"
    else 
        echo "failed to unmount..."
        echo "check for any open files: lsof $USB_MOUNT"
        exit 1
    fi
else
    echo "USB not mounted at $USB_MOUNT..."
fi