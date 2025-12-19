#!/bin/bash
# Complete RAG Evaluation Workflow with RAGAS (Local Chunking Version)
# This script executes three steps:
#   1. Upload documents to Milvus with LOCAL chunking (upload_with_local_chunking.py)
#   2. Generate RAG dataset with answers and contexts (rag.py)
#   3. Evaluate RAG quality with RAGAS metrics (evaluate_ragas.py)
#
# Uses local chunking for better control over chunk sizes (avoids 512 token limit issues)

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
EMBEDDING_MODEL="${EMBEDDING_MODEL:-multilingual-e5-large-vllm-embedding/multilingual-e5-large}"
EMBEDDING_DIMENSION="${EMBEDDING_DIMENSION:-476}"
DOCUMENTS_DIR="${RAGAS_DOCUMENTS_DIR:-${DOCUMENTS_DIR:-documents}}"
INPUT_DATASET="${INPUT_DATASET:-dataset-base/millbrook_dataset.json}"
OUTPUT_DATASET="${OUTPUT_DATASET:-output/millbrook_ragas_dataset.json}"
RESULTS_FILE="${RESULTS_FILE:-output/millbrook_ragas_results.json}"

# Advanced options
VERIFY_SSL="${VERIFY_SSL:-false}"

# Chunking configuration (LOCAL chunking for precise control)
# IMPORTANT: max_chunk_chars should be ~450 to stay under 512 tokens
CHUNK_SIZE="${CHUNK_SIZE:-400}"           # Target chunk size in characters
CHUNK_OVERLAP="${CHUNK_OVERLAP:-50}"      # Overlap between chunks
MAX_CHUNK_CHARS="${MAX_CHUNK_CHARS:-450}" # Hard limit (for embedding model's 512 token limit)

# Vector Store
VECTOR_STORE_ID="${RAGAS_VECTOR_STORE_ID:-${VECTOR_STORE_ID:-}}"
STORE_NAME="${STORE_NAME:-lrba_eval_$(date +%Y%m%d_%H%M%S)}"

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
echo "RAG EVALUATION WORKFLOW WITH RAGAS (Local Chunking)"
echo "======================================================================"
echo "Llama Stack URL:    $LLAMA_STACK_URL"
echo "LLM Model:          $MODEL_ID"
echo "Embedding Model:    $EMBEDDING_MODEL"
echo "Documents:          $DOCUMENTS_DIR"
echo "Chunk Size:         $CHUNK_SIZE chars"
echo "Chunk Overlap:      $CHUNK_OVERLAP chars"
echo "Max Chunk Chars:    $MAX_CHUNK_CHARS (hard limit)"
echo "Input Dataset:      $INPUT_DATASET"
echo "Output Dataset:     $OUTPUT_DATASET"
echo "Results File:       $RESULTS_FILE"
if [ -n "$VECTOR_STORE_ID" ]; then
    echo "Vector Store ID:    $VECTOR_STORE_ID (existing)"
else
    echo "Vector Store Name:  $STORE_NAME (new)"
fi
echo "======================================================================"
echo ""

# ============================================================================
# STEP 1: Upload Documents to Milvus with Local Chunking
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
    echo "STEP 1/3: Uploading Documents to Milvus (Local Chunking)"
    echo "======================================================================"
    echo ""
    
    # Run upload_with_local_chunking.py and capture the vector store ID
    UPLOAD_OUTPUT=$(python upload_with_local_chunking.py \
        --llama-stack-url "$LLAMA_STACK_URL" \
        --documents-dir "$DOCUMENTS_DIR" \
        --embedding-model "$EMBEDDING_MODEL" \
        --embedding-dimension "$EMBEDDING_DIMENSION" \
        --chunk-size "$CHUNK_SIZE" \
        --chunk-overlap "$CHUNK_OVERLAP" \
        --max-chunk-chars "$MAX_CHUNK_CHARS" \
        --store-name "$STORE_NAME" \
        --verify-query "LRBA" \
        2>&1)
    
    echo "$UPLOAD_OUTPUT"
    
    # Extract Vector Store ID from output
    VECTOR_STORE_ID=$(echo "$UPLOAD_OUTPUT" | grep -oP "Vector Store ID: \K[^ ]+" | tail -1)
    
    if [ -z "$VECTOR_STORE_ID" ]; then
        echo ""
        echo "❌ ERROR: Could not extract Vector Store ID from upload output"
        exit 1
    fi
    
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

# Check if input dataset exists, create sample if not
if [ ! -f "$INPUT_DATASET" ]; then
    echo "⚠️  Input dataset not found: $INPUT_DATASET"
    echo "   Creating a sample dataset..."
    mkdir -p "$(dirname "$INPUT_DATASET")"
    cat > "$INPUT_DATASET" << 'EOF'
{
  "questions": [
    {
      "question": "¿Qué es LRBA?",
      "ground_truth": "LRBA (Lightweight Runtime Architecture for Batch) es un runtime de arquitectura Ether para implementación de procesos de negocio por lotes o batch."
    }
  ]
}
EOF
    echo "   ✅ Sample dataset created: $INPUT_DATASET"
fi

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
echo "   VECTOR_STORE_ID=$VECTOR_STORE_ID ./run_evaluation.sh"
echo ""
echo "3. Test file_search manually:"
echo "   curl -k -X POST \"$LLAMA_STACK_URL/v1/responses\" \\"
echo "     -H \"Content-Type: application/json\" \\"
echo "     -d '{"
echo "       \"input\": \"¿Qué conectores hay en LRBA?\"," 
echo "       \"model\": \"$MODEL_ID\","
echo "       \"tools\": [{\"type\": \"file_search\", \"vector_store_ids\": [\"$VECTOR_STORE_ID\"]}]"
echo "     }'"
echo "======================================================================"
echo ""
