#!/bin/bash


set -e #exit on an error

echo "Starting USB Mounting Script..."

USERNAME="${USERNAME:-datalogger_364}"
USB_DEVICE="${USB_DEVICE:-/dev/sda1}" #defaulting to bottom left USB port
USB_ID="${USB_ID:-D4C1-015C}" #USB volume ID from lsblk -f

# Build paths from environment variables
USB_MOUNT="/media/$USERNAME/$USB_ID"
RAW_DIR="${RAW_DIR:-$USB_MOUNT/raw}"
FORMATTED_DIR="${FORMATTED_DIR:-$USB_MOUNT/processed}"

echo "Config:"
echo "  User: $USERNAME"
echo "  Device: $USB_DEVICE"
echo "  Mount: $USB_MOUNT"
echo "  Raw: $RAW_DIR"
echo "  Formatted: $FORMATTED_DIR"


#verify that the device exists
if [ ! -b "$USB_DEVICE" ]; then
    echo "ERROR: device $USB_DEVICE not found"
    echo "check USB connection, try running ls /dev/sd*"

    exit 1
fi 

#unmount USB if already mounted
if mount | grep -q "$USB_MOUNT"; then
    echo "USB already mounted at $USB_MOUNT"
    sudo umount "$USB_MOUNT" 2>/dev/null || true
    sudo rmdir "$USB_MOUNT" 2>/dev/null || true
fi

#create mount directory 
echo "creating mount directory: $USB_MOUNT"

sudo mkdir -p "$USB_MOUNT"
sudo chown "$USERNAME:$USERNAME" "$USB_MOUNT"

#mounting device
echo "Mounting $USB_DEVICE to $USB_MOUNT"

if sudo mount -o uid=$USERNAME,gid=$USERNAME "$USB_DEVICE" "$USB_MOUNT"; then
    echo "mount successful"
    echo "creating folder structure"

    mkdir -p "$RAW_DIR"
    mkdir -p "$FORMATTED_DIR"

    echo ""
    echo "   USB mounted successfully"
    echo "   Mount point: $USB_MOUNT"
    echo "   Raw data: $RAW_DIR"
    echo "   Processed files: $FORMATTED_DIR"
    echo ""
else
    echo "mount failed, try: sudo mount $USB_DEVICE $USB_MOUNT"
    exit 1
fi