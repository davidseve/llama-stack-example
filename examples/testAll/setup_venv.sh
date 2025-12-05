#!/bin/bash

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXAMPLES_DIR="$(dirname "$SCRIPT_DIR")"

echo "==================================="
echo "Setting up Virtual Environment"
echo "==================================="
echo "Examples dir: $EXAMPLES_DIR"
echo ""

# Remove old venv if exists
rm -rf "$SCRIPT_DIR/.venv"

# Create new venv
python3 -m venv "$SCRIPT_DIR/.venv"

# Activate venv
source "$SCRIPT_DIR/.venv/bin/activate"

# Upgrade pip
pip install --upgrade pip

# Install dependencies from both examples
echo ""
echo "Installing milvus-upload dependencies..."
pip install -r "$EXAMPLES_DIR/milvus-upload/requirements.txt"

echo ""
echo "Installing rag-mcp-chatbot dependencies..."
pip install -r "$EXAMPLES_DIR/rag-mcp-chatbot/requirements.txt"

echo ""
echo "Installing rag-evaluation-ragas dependencies..."
pip install -r "$EXAMPLES_DIR/rag-evaluation-ragas/requirements.txt"

echo ""
echo "==================================="
echo "✅ Virtual environment ready!"
echo "==================================="
echo ""
echo "To activate: source $SCRIPT_DIR/.venv/bin/activate"
echo ""
