#!/bin/bash

# Check if the script is run as root
if [[ $(/usr/bin/id -u) -ne 0 ]]; then
    echo "Not running as root"
    exit
fi

# Change directory to script directory
cd "$(dirname "$0")"

# Create a virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

# Activate the virtual environment
source .venv/bin/activate

# Install the required packages
pip3 install -r requirements.txt

# Copy systemd service files (exclude the template service file) from all directorys to /etc/systemd/system/
for service in $(find . -name "balloon-*.service" ! -name "balloon-template.service"); do
    cp "$service" /etc/systemd/system/
done

# Reload systemd
systemctl daemon-reload

# Enable the services
for service in /etc/systemd/system/balloon-*.service; do
    systemctl enable "$(basename "$service")"
done

# Create configuration file
if [ ! -f "config.yml" ]; then
    cp resources/templates/config.yml.example config.yml
fi
