#!/bin/bash

# Check if the script is run as root
if [[ $(/usr/bin/id -u) -ne 0 ]]; then
    echo "Not running as root"
    exit
fi

# Change directory to the parent of the script directory
cd "$(dirname "$0")/.."

# Check for virtual environment
if [ ! -d ".venv" ]; then
    echo "Environment not initialized, please run setup.sh first"
    exit
fi

# Start the services
for service in /etc/systemd/system/balloon-*.service; do
    echo "Starting service $(basename "$service")"
    systemctl start "$(basename "$service")"
done