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

# Check for service name argument
if [ -z "$1" ]; then
    echo "Stopping service balloon-$service.service"
    systemctl stop balloon-"$service".service
    exit
fi

# Stop all services
echo "No service name argument provided, stopping all services"
for service in /etc/systemd/system/balloon-*.service; do
    if [ "$service" == "/etc/systemd/system/balloon-*.service" ]; then
        echo "No systemd service files found"
        break
    fi
    echo "Stopping service $(basename "$service")"
    systemctl stop "$(basename "$service")"
done
