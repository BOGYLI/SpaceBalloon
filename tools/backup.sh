#!/bin/bash

# Check if the script is run as root
if [[ $(/usr/bin/id -u) -ne 0 ]]; then
    echo "Not running as root"
    exit
fi

# Change directory to the parent of the script directory
cd "$(dirname "$0")/.."

# Check for virtual environment and data directory
if [ ! -d ".venv" ] || [ ! -d "data" ]; then
    echo "Environment not initialized, please run setup.sh and reset.sh first"
    exit
fi

# Stop the services
for service in /etc/systemd/system/balloon-*.service; do
    if [ "$service" == "/etc/systemd/system/balloon-*.service" ]; then
        echo "No systemd service files found"
        break
    fi
    echo "Stopping service $(basename "$service")"
    systemctl stop "$(basename "$service")"
done

# Wait for stick insertion and user confirmation
echo "Please insert the USB stick (press enter to continue)"
read -r

# List all block devices and prompt user to select the correct one
lsblk
echo "Please select the USB stick e.g. /dev/sda1 (empty input to cancel)"
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

# Backup the sensor data directory with rclone
echo "Backing up the sensor data directory"
mkdir -p /mnt/balloon/data/sensor
rclone copy -P data/sensor /mnt/balloon/data/sensor

# Backup the video data directory with rclone
echo "Backing up the video data directory"
mkdir -p /mnt/balloon/data/video
rclone copy -P --ignore-existing data/video /mnt/balloon/data/video

# Unmount the USB stick
echo "Unmounting the USB stick"
umount /mnt/balloon

# Wait for stick removal and user confirmation
echo "Please remove the USB stick (press enter to continue)"
read -r

# Ask for the user confirmation to start the services
read -p "Do you want the services to start automatically? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Backup process completed"
    echo "Please start the services manually"
    exit
fi

# Start the services
for service in /etc/systemd/system/balloon-*.service; do
    if [ "$service" == "/etc/systemd/system/balloon-*.service" ]; then
        echo "No systemd service files found"
        break
    fi
    echo "Starting service $(basename "$service")"
    systemctl start "$(basename "$service")"
done

echo "Backup process completed"
