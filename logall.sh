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
    echo "Environment not initialized, please run setup.sh first"
    exit
fi

# Show logs of the services

for service in datamanager cammanager adc climate co2 gps magnet spectral system thermal \
        webcam0 webcam1 webcam2 webcam3 webcam4; do
    echo "Showing logs of $service service"
    splog $service
done

echo "Module service log check completed"
