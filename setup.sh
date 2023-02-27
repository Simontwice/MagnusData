#!/bin/bash

# Check if venv exists
if [[ -d "./venv" ]]; then
  echo "venv already exists. Activating venv and installing packages..."
  source ./venv/bin/activate
  pip install datasets pandas absl-py
else
  echo "Creating new virtual environment called venv and installing packages..."
  python3 -m venv venv
  source ./venv/bin/activate
  pip install datasets pandas absl-py
fi
