#!/bin/bash

# Change directory
cd ~/SpaceBalloon

# Set PYTHONPATH
export PYTHONPATH=~/SpaceBalloon

# Activate the virtual environment
source .venv/bin/activate

# Run init.py for all directories that contain it
for init in **/init.py; do
    python3 "$init"
done
