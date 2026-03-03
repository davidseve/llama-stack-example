#!/bin/bash
# MCP Chatbot - Kubernetes + ArgoCD Diagnostics
#
# This script runs a chatbot that uses MCP tools (Kubernetes and ArgoCD)
# to diagnose application issues. No RAG/vector store needed.
#
# The ArgoCD MCP server (SSE mode) needs credentials passed via HTTP headers.
# This script auto-fetches them from the K8s secret if available.

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
ARGOCD_MCP_NAMESPACE="${ARGOCD_MCP_NAMESPACE:-llama-stack-example}"
ARGOCD_MCP_SECRET="${ARGOCD_MCP_SECRET:-argocd-mcp-credentials}"

# Auto-fetch ArgoCD credentials from K8s secret if not already set
if [ -z "$ARGOCD_BASE_URL" ] || [ -z "$ARGOCD_API_TOKEN" ]; then
    if command -v oc &>/dev/null; then
        echo "Fetching ArgoCD credentials from secret ${ARGOCD_MCP_SECRET}..."
        export ARGOCD_BASE_URL=$(oc get secret "$ARGOCD_MCP_SECRET" -n "$ARGOCD_MCP_NAMESPACE" \
            -o jsonpath='{.data.ARGOCD_BASE_URL}' 2>/dev/null | base64 -d 2>/dev/null || true)
        export ARGOCD_API_TOKEN=$(oc get secret "$ARGOCD_MCP_SECRET" -n "$ARGOCD_MCP_NAMESPACE" \
            -o jsonpath='{.data.ARGOCD_API_TOKEN}' 2>/dev/null | base64 -d 2>/dev/null || true)
        if [ -n "$ARGOCD_BASE_URL" ]; then
            echo "  ArgoCD URL:   $ARGOCD_BASE_URL"
            echo "  ArgoCD Token: (loaded)"
        else
            echo "  WARNING: Could not fetch ArgoCD credentials. ArgoCD tools may not work."
        fi
    else
        echo "  WARNING: 'oc' not found and ARGOCD_BASE_URL not set. ArgoCD tools may not work."
    fi
fi

echo "======================================================================"
echo "LLAMA STACK CHATBOT - MCP Tools (Kubernetes + ArgoCD)"
echo "======================================================================"
echo "Server:           $REMOTE_BASE_URL"
echo "Model:            $INFERENCE_MODEL_ID"
echo "ArgoCD:           ${ARGOCD_BASE_URL:-(not configured)}"
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
