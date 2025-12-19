#!/usr/bin/env python3
"""
Upload documents to Milvus vector store using Llama Stack with LOCAL chunking.

This script uses the shared milvus-upload module with local chunking support.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

# Add parent directory to path to import shared module
sys.path.insert(0, str(Path(__file__).parent.parent / "milvus-upload"))

from milvus_upload import (
    MilvusLocalChunkingConfig,
    upload_documents_with_local_chunking,
    EMBEDDING_DIMENSIONS,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_CHUNK_OVERLAP,
    DEFAULT_MAX_CHUNK_CHARS,
)


# =============================================================================
# CONFIGURATION
# =============================================================================

LLAMA_STACK_URL = os.environ.get(
    "LLAMA_STACK_URL",
    "https://llama-stack-example-llama-stack-example.apps.ocp.sandbox5435.opentlc.com"
)

EMBEDDING_MODEL = os.environ.get(
    "EMBEDDING_MODEL",
    "granite-embedding-125m"
)

EMBEDDING_DIMENSION = int(os.environ.get("EMBEDDING_DIMENSION", "768"))


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Upload documents to Milvus with LOCAL chunking",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Available embedding models:
{chr(10).join(f'  - {model} ({dim} dim)' for model, dim in EMBEDDING_DIMENSIONS.items())}

⚠️ IMPORTANTE: El modelo de embedding DEBE coincidir con la configuración del servidor.

Examples:
  # Basic usage (uses documents/ directory)
  python milvus-upload.py
  
  # With custom chunk size
  python milvus-upload.py --chunk-size 500 --chunk-overlap 100
  
  # From JSON file
  python milvus-upload.py --json-file dataset.json
        """
    )
    
    parser.add_argument(
        "--documents-dir",
        type=Path,
        default=Path("documents"),
        help="Directory with documents to upload (default: documents)"
    )
    
    parser.add_argument(
        "--json-file",
        type=Path,
        help="JSON file with documents (alternative to --documents-dir)"
    )
    
    parser.add_argument(
        "--store-name",
        type=str,
        default=None,
        help="Name for the vector store (default: auto-generated with timestamp)"
    )
    
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=DEFAULT_CHUNK_SIZE,
        help=f"Chunk size in CHARACTERS (default: {DEFAULT_CHUNK_SIZE})"
    )
    
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=DEFAULT_CHUNK_OVERLAP,
        help=f"Overlap between chunks in characters (default: {DEFAULT_CHUNK_OVERLAP})"
    )
    
    parser.add_argument(
        "--url",
        "--llama-stack-url",
        type=str,
        default=LLAMA_STACK_URL,
        help="Llama Stack server URL"
    )
    
    parser.add_argument(
        "--embedding-model",
        type=str,
        default=EMBEDDING_MODEL,
        help=f"Embedding model (default: {EMBEDDING_MODEL})"
    )
    
    parser.add_argument(
        "--embedding-dimension",
        type=int,
        default=EMBEDDING_DIMENSION,
        help=f"Embedding dimension (default: {EMBEDDING_DIMENSION})"
    )
    
    parser.add_argument(
        "--verify-query",
        type=str,
        default="Millbrook",
        help="Query to verify insertion (default: Millbrook)"
    )
    
    parser.add_argument(
        "--batch-size",
        type=int,
        default=1,
        help="Batch size for insertion (default: 1, one by one)"
    )
    
    parser.add_argument(
        "--max-chunk-chars",
        type=int,
        default=DEFAULT_MAX_CHUNK_CHARS,
        help=f"Max characters per chunk (default: {DEFAULT_MAX_CHUNK_CHARS}, to avoid exceeding 512 tokens)"
    )
    
    parser.add_argument(
        "--verify-ssl",
        action="store_true",
        help="Enable SSL certificate verification (disabled by default)"
    )
    
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Timeout in seconds for requests (default: 300)"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        default=True,
        help="Show detailed progress"
    )
    
    args = parser.parse_args()
    
    # Generate store name if not provided
    store_name = args.store_name or f"rag_evaluation_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Create configuration
    config = MilvusLocalChunkingConfig(
        llama_stack_url=args.url,
        documents_dir=str(args.documents_dir),
        json_file=str(args.json_file) if args.json_file else None,
        embedding_model=args.embedding_model,
        embedding_dimension=args.embedding_dimension,
        vector_store_name=store_name,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
        max_chunk_chars=args.max_chunk_chars,
        batch_size=args.batch_size,
        verify_ssl=args.verify_ssl,
        timeout=args.timeout,
        verbose=args.verbose,
        verify_query=args.verify_query,
    )
    
    try:
        result = upload_documents_with_local_chunking(config)
        
        vector_store_id = result["vector_store_id"]
        
        print()
        print("   📝 Next steps:")
        print(f"   Use this Vector Store ID in rag.py:")
        print(f"\n   export VECTOR_STORE_ID={vector_store_id}")
        print(f"   python rag.py")
        print()
        print("   Para usar con file_search:")
        print(f'   curl -k -X POST "{args.url}/v1/responses" \\')
        print('     -H "Content-Type: application/json" \\')
        print('     -d \'{')
        print('       "input": "tu pregunta aquí",')
        print('       "model": "your-model-id",')
        print('       "tools": [{"type": "file_search", "vector_store_ids": ["' + vector_store_id + '"]}]')
        print("     }'")
        print()
        
        # Save vector store info
        output_info = {
            **result,
            "timestamp": datetime.now().isoformat()
        }
        
        output_file = Path("output") / f"{store_name}_info.json"
        output_file.parent.mkdir(exist_ok=True)
        with open(output_file, "w") as f:
            json.dump(output_info, f, indent=2)
        print(f"   📝 Info saved to: {output_file}")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        import traceback
        print("\n📋 Full traceback:", file=sys.stderr)
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
