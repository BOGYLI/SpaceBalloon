#!/bin/bash

# Check if the script is run as root
if [[ $(/usr/bin/id -u) -ne 0 ]]; then
    echo "Not running as root"
    exit
fi

# Change directory to script directory
cd "$(dirname "$0")"

# Start the services
for service in /etc/systemd/system/balloon-*.service; do
    systemctl start "$(basename "$service")"
done
