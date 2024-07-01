#!/bin/bash

# Check if the script is run as root
if [[ $(/usr/bin/id -u) -ne 0 ]]; then
    echo "Not running as root"
    exit
fi

# Change directory to script directory
cd "$(dirname "$0")"

# Set PYTHONPATH
export PYTHONPATH="$(dirname "$0")"

# Activate the virtual environment
source .venv/bin/activate

# Run init.py for all directories that contain it (exclude template)
for init in $(find . -name "init.py" ! -path "./template/*"); do
    python3 "$init"
done
