#!/bin/bash

# Change directory
cd ~/SpaceBalloon

# Set PYTHONPATH
export PYTHONPATH=~/SpaceBalloon

# Activate the virtual environment
source .venv/bin/activate

# Start python script
python3 template/main.py
