#!/bin/bash
# MCP Chatbot - Kubernetes + ArgoCD Diagnostics
#
# This script runs a chatbot that uses MCP tools (Kubernetes and ArgoCD)
# to diagnose application issues. No RAG/vector store needed.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXAMPLES_DIR="$(dirname "$SCRIPT_DIR")"

if [ -f "$SCRIPT_DIR/.venv/bin/activate" ]; then
    source "$SCRIPT_DIR/.venv/bin/activate"
fi

if [ -f "$EXAMPLES_DIR/.env" ]; then
    echo "Loading configuration from examples/.env..."
    set -a
    source "$EXAMPLES_DIR/.env"
    set +a
else
    echo "No .env found. Copy env.template to .env:"
    echo "   cp $EXAMPLES_DIR/env.template $EXAMPLES_DIR/.env"
    exit 1
fi

REMOTE_BASE_URL="${REMOTE_BASE_URL:-http://localhost:8321}"
INFERENCE_MODEL_ID="${INFERENCE_MODEL_ID:-granite32-8b}"

echo "======================================================================"
echo "LLAMA STACK CHATBOT - MCP Tools (Kubernetes + ArgoCD)"
echo "======================================================================"
echo "Server:           $REMOTE_BASE_URL"
echo "Model:            $INFERENCE_MODEL_ID"
echo "======================================================================"
echo ""

python chatbot.py || {
    echo "ERROR: chatbot.py failed"
    exit 1
}

echo ""
echo "======================================================================"
echo "COMPLETED"
echo "======================================================================"
