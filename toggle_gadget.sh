#!/bin/bash

RIG_CONTAINER_FILE="${RIG_CONTAINER_FILE:-/home/datalogger364/pi-sharepoint-upload/rig_data_container.bin}"

if [ "$1" = "stop" ]; then
    echo "turning off gadget mode"
    sudo rmmod g_mass_storage
elif [ "$1" = "start" ]; then
    echo "turning on gadget mode"
    sudo modprobe g_mass_storage file=${RIG_CONTAINER_FILE} stall=0 ro=0
else
    echo "usage: $0 {start|stop}"
fi