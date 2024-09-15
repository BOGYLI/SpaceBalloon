#!/bin/bash

# Check if the script is run as root
if [[ $(/usr/bin/id -u) -ne 0 ]]; then
    echo "Not running as root"
    exit
fi

# Change directory to script directory
cd "$(dirname "$0")"

# Check for virtual environment and data directory
if [ ! -d ".venv" ] || [ ! -d "data" ]; then
    echo "Environment not initialized, please run setup.sh and reset.sh first"
    exit
fi

# Stop the services
for service in /etc/systemd/system/balloon-*.service; do
    echo "Stopping service $(basename "$service")"
    systemctl stop "$(basename "$service")"
done

# Wait for stick insertion and user confirmation
echo "Please insert the USB stick (press enter to continue)"
read -r

# List all block devices and prompt user to select the correct one
lsblk
echo "Please select the USB stick e.g. /dev/sdb (empty input to cancel)"
read -r -p "> " usb_stick

# Check if the input is empty
if [ -z "$usb_stick" ]; then
    echo "No USB stick selected, cancel backup process"
    echo "Please start the services manually"
    exit
fi

# Mount the USB stick
echo "Mounting the USB stick"
mkdir -p /mnt/balloon
mount "$usb_stick" /mnt/balloon

# Backup the data directory with rclone
echo "Backing up the data directory"
mkdir /mnt/balloon/data
rclone copy -P data /mnt/balloon/data

# Unmount the USB stick
echo "Unmounting the USB stick"
umount /mnt/balloon

# Wait for stick removal and user confirmation
echo "Please remove the USB stick (press enter to continue)"
read -r

# Start the services
for service in /etc/systemd/system/balloon-*.service; do
    echo "Starting service $(basename "$service")"
    systemctl start "$(basename "$service")"
done

echo "Backup process completed"
