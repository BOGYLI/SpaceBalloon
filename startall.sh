#!/bin/bash

# Change directory
cd ~/SpaceBalloon

# Start the services
for service in /etc/systemd/system/balloon-*.service; do
    systemctl start "$(basename "$service")"
done
