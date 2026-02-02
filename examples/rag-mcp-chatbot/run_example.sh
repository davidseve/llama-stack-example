#!/bin/bash
# Chatbot with RAG + MCP Tools - Complete Workflow
#
# This script:
#   1. Uploads documents to Milvus (if needed)
#   2. Runs the chatbot with a test query

set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXAMPLES_DIR="$(dirname "$SCRIPT_DIR")"

# Activate virtual environment if it exists
if [ -f "$SCRIPT_DIR/.venv/bin/activate" ]; then
    source "$SCRIPT_DIR/.venv/bin/activate"
fi

# Load configuration from examples/.env
if [ -f "$EXAMPLES_DIR/.env" ]; then
    echo "📝 Loading configuration from examples/.env..."
    set -a
    source "$EXAMPLES_DIR/.env"
    set +a
else
    echo "⚠️  No .env found. Copy env.template to .env:"
    echo "   cp $EXAMPLES_DIR/env.template $EXAMPLES_DIR/.env"
fi

# Configuration
REMOTE_BASE_URL="${REMOTE_BASE_URL:-http://localhost:8321}"
INFERENCE_MODEL_ID="${INFERENCE_MODEL_ID:-granite32-8b}"
EMBEDDING_MODEL="${EMBEDDING_MODEL:-granite-embedding-125m}"
DOCUMENTS_DIR="${MCP_DOCUMENTS_DIR:-${DOCUMENTS_DIR:-documents}}"
# Use MCP-specific vector store ID
VECTOR_STORE_ID="${MCP_VECTOR_STORE_ID:-${VECTOR_STORE_ID:-}}"

echo "======================================================================"
echo "LLAMA STACK CHATBOT - RAG + MCP"
echo "======================================================================"
echo "Server:           $REMOTE_BASE_URL"
echo "Model:            $INFERENCE_MODEL_ID"
echo "Embedding Model:  $EMBEDDING_MODEL"
echo "Documents:        $DOCUMENTS_DIR"
echo "Vector Store ID:  ${VECTOR_STORE_ID:-<will be created>}"
echo "======================================================================"
echo ""

# ============================================================================
# STEP 1: Upload Documents (if VECTOR_STORE_ID not set)
# ============================================================================
if [ -z "$VECTOR_STORE_ID" ]; then
    echo "======================================================================"
    echo "STEP 1/2: Uploading Documents to Milvus"
    echo "======================================================================"
    echo ""
    
    UPLOAD_OUTPUT=$(python milvus-upload.py \
        --url "$REMOTE_BASE_URL" \
        --documents-dir "$DOCUMENTS_DIR" \
        --embedding-model "$EMBEDDING_MODEL" \
        --max-chunk-chars 2000 \
        --chunk-size 2000 \
        --chunk-overlap 200 \
        $([ "$VERIFY_SSL" = "true" ] && echo "--verify-ssl") \
        2>&1) || {
        echo "$UPLOAD_OUTPUT"
        echo "❌ ERROR: milvus-upload.py failed"
        exit 1
    }
    
    echo "$UPLOAD_OUTPUT"
    
    # Extract Vector Store ID
    VECTOR_STORE_ID=$(echo "$UPLOAD_OUTPUT" | grep -oP "Vector Store ID: \K[^ ]+$" | tail -1)
    
    if [ -z "$VECTOR_STORE_ID" ]; then
        echo "❌ ERROR: Could not extract Vector Store ID"
        exit 1
    fi
    
    # Save to shared .env for future runs
    echo "MCP_VECTOR_STORE_ID=$VECTOR_STORE_ID" >> "$EXAMPLES_DIR/.env"
    export VECTOR_STORE_ID
    
    echo ""
    echo "✅ Step 1 Complete - Vector Store ID: $VECTOR_STORE_ID"
    echo ""
else
    echo "======================================================================"
    echo "STEP 1/2: Using Existing Vector Store"
    echo "======================================================================"
    echo "📌 Vector Store ID: $VECTOR_STORE_ID"
    echo "⏭️  Skipping document upload"
    export VECTOR_STORE_ID
    echo ""
fi

# ============================================================================
# STEP 2: Run Chatbot
# ============================================================================
echo "======================================================================"
echo "STEP 2/2: Running Chatbot"
echo "======================================================================"
echo ""

python chatbot.py || {
    echo "❌ ERROR: chatbot.py failed"
    exit 1
}

echo ""
echo "======================================================================"
echo "✅ COMPLETED"
echo "======================================================================"
echo ""
echo "📝 To run again without re-uploading:"
echo "   VECTOR_STORE_ID=$VECTOR_STORE_ID python chatbot.py"
echo ""
echo "📝 Or save to .env:"
echo "   echo 'VECTOR_STORE_ID=$VECTOR_STORE_ID' >> .env"
echo "   python chatbot.py"
echo "======================================================================"

