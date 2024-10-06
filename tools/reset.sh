#!/bin/bash

# Check if the script is run as root
if [[ $(/usr/bin/id -u) -ne 0 ]]; then
    echo "Not running as root"
    exit
fi

# Change directory to the parent of the script directory
cd "$(dirname "$0")/.."

# Set PYTHONPATH
export PYTHONPATH="$(dirname "$0")/.."

# Check for virtual environment
if [ ! -d ".venv" ]; then
    echo "Environment not initialized, please run setup.sh first"
    exit
fi

# Ask for confirmation
echo "WARNING! You are about to delete all existing sensor data and video footage!"
echo "This action cannot be undone. It isn't recommended to automatically run this script."
read -p "Are you sure to continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit
fi

# Activate the virtual environment
source .venv/bin/activate

# Run init.py for all directories that contain it (exclude template)
for init in $(find . -name "init.py" ! -path "./resources/templates/*"); do
    echo "Running $init"
    python3 "$init"
done
