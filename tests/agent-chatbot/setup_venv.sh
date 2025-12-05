#!/bin/bash
# Setup virtual environment with llama-stack-client 0.2.17 (matching server version)

echo "==================================="
echo "Setting up Virtual Environment"
echo "Target: llama-stack-client 0.3.3 (compatible with server 0.3.0rc3)"
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

