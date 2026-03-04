#!/bin/bash

echo "==================================="
echo "Setting up Virtual Environment"
echo "==================================="

# Remove old venv if exists
rm -rf .venv

# Create new venv
python3 -m venv .venv

# Activate venv
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt

