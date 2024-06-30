#!/bin/bash

# Change directory
cd ~/SpaceBalloon

# Stop the services
for service in /etc/systemd/system/balloon-*.service; do
    systemctl stop "$(basename "$service")"
done
