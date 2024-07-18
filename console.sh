#!/bin/bash

# Change directory to the console script directory
cd "$(dirname "$0")"/cmd

# Set PYTHONPATH
export PYTHONPATH="$(dirname "$0")"/cmd

# Create a virtual environment and install required packages if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment"
    python3 -m venv .venv

    # Activate the virtual environment
    source .venv/bin/activate

    # Install the required packages
    echo "Installing required packages"
    pip3 install requests
else
    # Activate the virtual environment else
    source .venv/bin/activate
fi

# Start python script
python3 main.py
