#!/bin/bash
# Complete RAG Evaluation Workflow with RAGAS
# This script executes three steps:
#   1. Upload documents to Milvus (milvus-upload.py)
#   2. Generate RAG dataset with answers and contexts (rag.py)
#   3. Evaluate RAG quality with RAGAS metrics (evaluate_ragas.py)
#
# Based on Red Hat OpenShift AI Self-Managed 3.0 best practices

set -e  # Exit on error

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXAMPLES_DIR="$(dirname "$SCRIPT_DIR")"

# ============================================================================
# Configuration
# ============================================================================

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

# Use REMOTE_BASE_URL as fallback for LLAMA_STACK_URL
LLAMA_STACK_URL="${LLAMA_STACK_URL:-${REMOTE_BASE_URL:-https://llama-stack-example-llama-stack-example.apps.ocp.sandbox5435.opentlc.com}}"
MODEL_ID="${MODEL_ID:-${INFERENCE_MODEL_ID:-vllm-inference/llama-4-scout-17b-16e-w4a16}}"
EMBEDDING_MODEL="${EMBEDDING_MODEL:-granite-embedding-125m}"
DOCUMENTS_DIR="${RAGAS_DOCUMENTS_DIR:-${DOCUMENTS_DIR:-documents}}"
INPUT_DATASET="${INPUT_DATASET:-dataset-base/millbrook_dataset.json}"
OUTPUT_DATASET="${OUTPUT_DATASET:-output/millbrook_ragas_dataset.json}"
RESULTS_FILE="${RESULTS_FILE:-output/millbrook_ragas_results.json}"

# Advanced options
VERIFY_SSL="${VERIFY_SSL:-false}"
# Evaluation mode: "inline" (default) or "remote" (requires DSPA/Kubeflow)
RAGAS_MODE="${RAGAS_MODE:-inline}"
# Use RAGAS-specific vector store ID
VECTOR_STORE_ID="${RAGAS_VECTOR_STORE_ID:-${VECTOR_STORE_ID:-}}"

# ============================================================================
# Helper: Validate vector store exists on the server
# ============================================================================
validate_vector_store() {
    local vs_id="$1"
    local url="$2"
    local ssl_flag=""
    if [ "$VERIFY_SSL" != "true" ]; then
        ssl_flag="--insecure"
    fi

    # Try to GET the vector store from the server
    local http_code
    http_code=$(curl -s -o /dev/null -w "%{http_code}" $ssl_flag \
        "${url}/v1/vector_stores/${vs_id}" 2>/dev/null) || true

    if [ "$http_code" = "200" ]; then
        return 0  # Vector store exists
    else
        return 1  # Vector store not found or server error
    fi
}

# Helper: Update or add a key in .env without creating duplicates
update_env_key() {
    local key="$1"
    local value="$2"
    local env_file="$3"

    if grep -q "^${key}=" "$env_file" 2>/dev/null; then
        # Update existing entry
        sed -i "s|^${key}=.*|${key}=${value}|" "$env_file"
    else
        # Append new entry
        echo "${key}=${value}" >> "$env_file"
    fi
}

# Auto-detect if we should skip upload based on VECTOR_STORE_ID
SKIP_UPLOAD="${SKIP_UPLOAD:-false}"
if [ -n "$VECTOR_STORE_ID" ]; then
    echo "🔍 Validating existing vector store: $VECTOR_STORE_ID ..."
    if validate_vector_store "$VECTOR_STORE_ID" "$LLAMA_STACK_URL"; then
        echo "✅ Vector store exists on the server"
        SKIP_UPLOAD="true"
    else
        echo "⚠️  Vector store $VECTOR_STORE_ID not found on server (stale ID)"
        echo "   Will create a new vector store..."
        VECTOR_STORE_ID=""
        SKIP_UPLOAD="false"
    fi
fi

# ============================================================================
# Print Configuration
# ============================================================================
echo "======================================================================"
echo "RAG EVALUATION WORKFLOW WITH RAGAS"
echo "======================================================================"
echo "Llama Stack URL:    $LLAMA_STACK_URL"
echo "Model:              $MODEL_ID"
echo "Embedding Model:    $EMBEDDING_MODEL"
echo "RAGAS Mode:         $RAGAS_MODE"
echo "Documents:          $DOCUMENTS_DIR"
echo "Input Dataset:      $INPUT_DATASET"
echo "Output Dataset:     $OUTPUT_DATASET"
echo "Results File:       $RESULTS_FILE"
echo "======================================================================"
echo ""

# ============================================================================
# STEP 1: Upload Documents to Milvus
# ============================================================================
if [ "$SKIP_UPLOAD" = "true" ] && [ -n "$VECTOR_STORE_ID" ]; then
    echo "======================================================================"
    echo "STEP 1/3: Using Existing Vector Store (Skipping Upload)"
    echo "======================================================================"
    echo ""
    echo "⏭️  Skipping document upload (Vector Store ID already configured)"
    echo "📌 Using Vector Store ID: $VECTOR_STORE_ID"
    echo ""
    echo "✅ Step 1 Skipped - Using existing vector store"
    echo ""
else
    echo "======================================================================"
    echo "STEP 1/3: Uploading Documents to Milvus"
    echo "======================================================================"
    echo ""
    
    # Run milvus-upload.py and capture the vector store ID
    UPLOAD_OUTPUT=$(python milvus-upload.py \
        --url "$LLAMA_STACK_URL" \
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
    
    # Extract Vector Store ID from output
    VECTOR_STORE_ID=$(echo "$UPLOAD_OUTPUT" | grep -oP "Vector Store ID: \K[^ ]+$" | tail -1)
    
    if [ -z "$VECTOR_STORE_ID" ]; then
        echo ""
        echo "❌ ERROR: Could not extract Vector Store ID from upload output"
        exit 1
    fi
    
    # Save to shared .env for future runs (update in-place, no duplicates)
    update_env_key "RAGAS_VECTOR_STORE_ID" "$VECTOR_STORE_ID" "$EXAMPLES_DIR/.env"
    
    echo ""
    echo "✅ Step 1 Complete - Vector Store ID: $VECTOR_STORE_ID"
    echo ""
fi

# ============================================================================
# STEP 2: Generate RAG Dataset
# ============================================================================
echo "======================================================================"
echo "STEP 2/3: Generating RAG Dataset with Answers and Contexts"
echo "======================================================================"
echo ""

python rag.py \
    --url "$LLAMA_STACK_URL" \
    --model-id "$MODEL_ID" \
    --vector-store-id "$VECTOR_STORE_ID" \
    --input "$INPUT_DATASET" \
    --output "$OUTPUT_DATASET" \
    $([ "$VERIFY_SSL" = "true" ] && echo "--verify-ssl") || {
    echo "❌ ERROR: rag.py failed"
    exit 1
}

echo ""
echo "✅ Step 2 Complete - RAG dataset saved to: $OUTPUT_DATASET"
echo ""

# ============================================================================
# STEP 3: Evaluate with RAGAS
# ============================================================================
echo "======================================================================"
echo "STEP 3/3: Evaluating RAG Quality with RAGAS Metrics"
echo "======================================================================"
echo ""

python evaluate_ragas.py \
    --url "$LLAMA_STACK_URL" \
    --model-id "$MODEL_ID" \
    --dataset "$OUTPUT_DATASET" \
    --output "$RESULTS_FILE" \
    --mode "$RAGAS_MODE" \
    --batch-size 1 \
    --max-wait 300 \
    $([ "$VERIFY_SSL" = "true" ] && echo "--verify-ssl") || {
    echo "❌ ERROR: evaluate_ragas.py failed"
    exit 1
}

echo ""
echo "✅ Step 3 Complete - Evaluation results saved to: $RESULTS_FILE"
echo ""

# ============================================================================
# Summary
# ============================================================================
echo "======================================================================"
echo "🎉 WORKFLOW COMPLETED SUCCESSFULLY!"
echo "======================================================================"
echo ""
echo "📊 Generated Files:"
echo "   - RAG Dataset:    $OUTPUT_DATASET"
echo "   - RAGAS Results:  $RESULTS_FILE"
echo ""
echo "🔍 Vector Store ID:  $VECTOR_STORE_ID"
echo ""
echo "======================================================================"
echo "Next Steps:"
echo "======================================================================"
echo "1. Review the RAGAS evaluation results:"
echo "   cat $RESULTS_FILE | jq '.metrics'"
echo ""
echo "2. Re-run evaluation without re-uploading documents:"
echo "   RAGAS_VECTOR_STORE_ID=$VECTOR_STORE_ID ./run_example.sh"
echo ""
echo "3. Use REMOTE mode (requires DSPA/Kubeflow):"
echo "   RAGAS_MODE=remote ./run_example.sh"
echo ""
echo "4. Evaluate with specific metrics only:"
echo "   python evaluate_ragas.py --dataset $OUTPUT_DATASET \\"
echo "       --metrics answer_relevancy faithfulness --mode inline"
echo "======================================================================"
echo ""

