#!/bin/bash

# Check if the script is run as root
if [[ $(/usr/bin/id -u) -ne 0 ]]; then
    echo "Not running as root"
    exit
fi

# Change directory to the parent of the script directory
cd "$(dirname "$0")/.."

# Ask for the user confirmation to uninstall this environment
echo "You are about to uninstall this environment"
echo "This will remove the python virtual environment,"
echo "configuration, systemd service files and data storage"
read -p "Are you sure? (y/n) " -n 1 -r
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit
fi

# Remove systemd service files
for service in /etc/systemd/system/balloon-*.service; do
    if [ "$service" == "/etc/systemd/system/balloon-*.service" ]; then
        echo "No systemd service files found"
        break
    fi
    echo "Removing service $(basename "$service")"
    systemctl stop "$(basename "$service")"
    systemctl disable "$(basename "$service")"
    rm "$service"
done

# Reload systemd
echo "Reloading systemd"
systemctl daemon-reload

# Remove python virtual environment
if [ -d ".venv" ]; then
    echo "Removing python virtual environment"
    rm -r .venv
fi

# Remove configuration file
if [ -f "config.yml" ]; then
    echo "Removing configuration file"
    rm config.yml
fi

# Ask for confirmation before deleting data storage
echo "WARNING! You are about to delete all existing sensor data and video footage!"
echo "This action cannot be undone. It isn't recommended to automatically run this script."
read -p "Are you sure to continue? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Removing data storage"
    rm -r data
fi

# Futher instructions
echo "Environment uninstalled"
echo "It is now safe to delete the repository folder"
echo "Thank you and goodbye :)"
echo "(Reinstall everything with setup.sh)"
