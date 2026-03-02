#!/bin/bash
# Guardrails Test Workflow
# Tests all guardrail detectors via the Llama Stack Responses API:
#   - Regex filter
#   - HAP (Hate, Abuse, Profanity)
#   - Prompt injection detection
#   - Language detection
#
# Prerequisites:
#   - Llama Stack deployed with guardrails enabled
#   - Guardrails Orchestrator deployed

set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXAMPLES_DIR="$(dirname "$SCRIPT_DIR")"

# ============================================================================
# Configuration
# ============================================================================

# Load configuration from examples/.env
if [ -f "$EXAMPLES_DIR/.env" ]; then
    echo "Loading configuration from examples/.env..."
    set -a
    source "$EXAMPLES_DIR/.env"
    set +a
else
    echo "No .env found. Copy env.template to .env:"
    echo "   cp $EXAMPLES_DIR/env.template $EXAMPLES_DIR/.env"
fi

LLAMA_STACK_URL="${LLAMA_STACK_URL:-${REMOTE_BASE_URL:-}}"
MODEL_ID="${MODEL_ID:-${INFERENCE_MODEL_ID:-}}"
VERIFY_SSL="${VERIFY_SSL:-false}"

if [ -z "$LLAMA_STACK_URL" ]; then
    echo "ERROR: LLAMA_STACK_URL is required. Set it in examples/.env or as environment variable."
    exit 1
fi

if [ -z "$MODEL_ID" ]; then
    echo "ERROR: MODEL_ID is required. Set it in examples/.env or as environment variable."
    exit 1
fi

# ============================================================================
# Setup virtual environment
# ============================================================================
if [ ! -d "$SCRIPT_DIR/.venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$SCRIPT_DIR/.venv"
fi

source "$SCRIPT_DIR/.venv/bin/activate"
pip install -q -r "$SCRIPT_DIR/requirements.txt"

# ============================================================================
# Print Configuration
# ============================================================================
echo "======================================================================"
echo "GUARDRAILS TEST SUITE"
echo "======================================================================"
echo "Llama Stack URL:  $LLAMA_STACK_URL"
echo "Model:            $MODEL_ID"
echo "Verify SSL:       $VERIFY_SSL"
echo "======================================================================"
echo ""

# ============================================================================
# Run Tests
# ============================================================================
SSL_FLAG=""
if [ "$VERIFY_SSL" = "true" ]; then
    SSL_FLAG="--verify-ssl"
fi

python "$SCRIPT_DIR/test_guardrails.py" \
    --url "$LLAMA_STACK_URL" \
    --model "$MODEL_ID" \
    $SSL_FLAG \
    "$@"

echo ""
echo "======================================================================"
echo "Done!"
echo "======================================================================"
