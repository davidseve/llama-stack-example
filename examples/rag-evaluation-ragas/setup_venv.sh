#!/bin/bash
# Setup virtual environment for LLS 0.5.x

echo "==================================="
echo "Setting up Virtual Environment"
echo "Target: llama-stack-client >=0.5.0 (compatible with server 0.5.x)"
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

echo ""
echo "==================================="
echo "Installed versions:"
echo "==================================="
pip list | grep -E "(llama-stack|httpx)"

echo ""
echo "==================================="
echo "Virtual environment ready!"
echo "==================================="
echo ""
echo "Server version: Llama Stack 0.5.x"
echo "Client version: llama-stack-client >=0.5.0"
echo ""
echo "To activate:"
echo "  source .venv/bin/activate"
echo ""
echo "To test:"
echo "  RAGAS_MODE=inline ./run_example.sh"
echo "  RAGAS_MODE=remote ./run_example.sh"
echo ""

