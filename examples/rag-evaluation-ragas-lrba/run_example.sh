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
# Chunking configuration (client-side chunking for precise control)
# IMPORTANT: For multilingual models, 1 token ≈ 2-3 characters!
# For 512-token limit: use ~200 chars (conservative)
CHUNK_SIZE="${CHUNK_SIZE:-200}"       # Chunk size in characters
CHUNK_OVERLAP="${CHUNK_OVERLAP:-20}"  # Overlap between chunks
# Milvus mode: "inline" (embedded/local) or "remote" (external Milvus server)
MILVUS_MODE="${MILVUS_MODE:-inline}"
# Use RAGAS-specific vector store ID
VECTOR_STORE_ID="${RAGAS_VECTOR_STORE_ID:-${VECTOR_STORE_ID:-}}"

# Auto-detect if we should skip upload based on VECTOR_STORE_ID
if [ -n "$VECTOR_STORE_ID" ]; then
    SKIP_UPLOAD="true"
else
    SKIP_UPLOAD="${SKIP_UPLOAD:-false}"
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
echo "Documents:          $DOCUMENTS_DIR"
echo "Chunk Size:         $CHUNK_SIZE chars"
echo "Chunk Overlap:      $CHUNK_OVERLAP chars"
echo "Milvus Mode:        $MILVUS_MODE"
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
        --chunk-size "$CHUNK_SIZE" \
        --chunk-overlap "$CHUNK_OVERLAP" \
        --milvus-mode "$MILVUS_MODE" \
        $([ "$VERIFY_SSL" = "true" ] && echo "--verify-ssl") \
        2>&1)
    
    echo "$UPLOAD_OUTPUT"
    
    # Extract Vector Store ID from output
    # Extract Vector Store ID from output (supports both "Vector Store ID:" and "Vector DB ID:")
    VECTOR_STORE_ID=$(echo "$UPLOAD_OUTPUT" | grep -oP "(Vector Store ID|Vector DB ID): \K[^ ]+$" | tail -1)
    
    if [ -z "$VECTOR_STORE_ID" ]; then
        echo ""
        echo "❌ ERROR: Could not extract Vector Store ID from upload output"
        exit 1
    fi
    
    # Save to shared .env for future runs
    echo "RAGAS_VECTOR_STORE_ID=$VECTOR_STORE_ID" >> "$EXAMPLES_DIR/.env"
    
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
    $([ "$VERIFY_SSL" = "true" ] && echo "--verify-ssl")

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
    --batch-size 1 \
    $([ "$VERIFY_SSL" = "true" ] && echo "--verify-ssl")

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
echo "3. Evaluate with specific metrics only:"
echo "   python evaluate_ragas.py --dataset $OUTPUT_DATASET \\"
echo "       --metrics answer_relevancy faithfulness --batch-size 1"
echo "======================================================================"
echo ""

