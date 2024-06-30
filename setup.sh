#!/bin/bash

# Change directory
cd ~/SpaceBalloon

# Create a virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

# Activate the virtual environment
source .venv/bin/activate

# Install the required packages
pip3 install -r requirements.txt

# Copy systemd service files from all directorys to /etc/systemd/system
cp **/*.service /etc/systemd/system/

# Reload systemd
systemctl daemon-reload

# Enable the services
for service in /etc/systemd/system/balloon-*.service; do
    systemctl enable "$(basename "$service")"
done

# Create configuration file
if [ ! -f "config.yml" ]; then
    cp resources/config.yml.example config.yml
fi
