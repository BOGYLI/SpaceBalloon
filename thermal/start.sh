#!/bin/bash

# Check if the script is run as root
if [[ $(/usr/bin/id -u) -ne 0 ]]; then
    echo "Not running as root"
    exit
fi

# Change directory to the parent of the script directory
cd "$(dirname "$0")"/..

# Set PYTHONPATH
export PYTHONPATH="$(dirname "$0")"/..

# Activate the virtual environment
source .venv/bin/activate

# Start python script with priority scheduling
nice -n -10 python3 thermal/main.py
