#!/bin/bash

set -e 

USERNAME="${USERNAME:-dataloggerX}"
USB_MOUNT="${USB_MOUNT:-/media/${USERNAME}/usb_formatted_data}" #note: same as formatted_dir

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