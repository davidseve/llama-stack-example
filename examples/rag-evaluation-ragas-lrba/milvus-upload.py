#!/usr/bin/env python3
"""
Upload documents to Milvus vector store using Llama Stack.

This script uses the shared milvus-upload module.
"""

import os
import sys
import argparse
from pathlib import Path

# Add parent directory to path to import shared module
sys.path.insert(0, str(Path(__file__).parent.parent / "milvus-upload"))

from milvus_upload import (
    MilvusUploadConfig, 
    upload_documents_to_milvus,
    EMBEDDING_DIMENSIONS,
    MILVUS_MODE_INLINE,
    MILVUS_MODE_REMOTE,
    MILVUS_PROVIDER_IDS,
)


def main():
    parser = argparse.ArgumentParser(
        description="Upload documents to Milvus using Llama Stack",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Available embedding models:
{chr(10).join(f'  - {model} ({dim} dim)' for model, dim in EMBEDDING_DIMENSIONS.items())}

Milvus modes:
  - inline: Use embedded/local Milvus (provider: {MILVUS_PROVIDER_IDS[MILVUS_MODE_INLINE]})
  - remote: Use external Milvus server (provider: {MILVUS_PROVIDER_IDS[MILVUS_MODE_REMOTE]})

Example:
  python milvus-upload.py --embedding-model granite-embedding-125m
  python milvus-upload.py --remote --embedding-model granite-embedding-125m
        """
    )
    parser.add_argument(
        "--url",
        default="https://llama-stack-example-llama-stack-example.apps.ocp.sandbox5435.opentlc.com",
        help="Llama Stack URL (default: OpenShift sandbox)"
    )
    parser.add_argument(
        "--documents-dir",
        default="documents",
        help="Directory containing documents (default: documents)"
    )
    parser.add_argument(
        "--embedding-model",
        default="granite-embedding-125m",
        help="Embedding model to use (default: granite-embedding-125m)"
    )
    # Milvus mode selection
    milvus_group = parser.add_mutually_exclusive_group()
    milvus_group.add_argument(
        "--milvus-mode",
        choices=[MILVUS_MODE_INLINE, MILVUS_MODE_REMOTE],
        default=os.getenv("MILVUS_MODE", MILVUS_MODE_INLINE),
        help=f"Milvus mode: '{MILVUS_MODE_INLINE}' for embedded or '{MILVUS_MODE_REMOTE}' for external server"
    )
    milvus_group.add_argument(
        "--remote",
        action="store_true",
        help=f"Shorthand for --milvus-mode {MILVUS_MODE_REMOTE}"
    )
    milvus_group.add_argument(
        "--inline",
        action="store_true",
        help=f"Shorthand for --milvus-mode {MILVUS_MODE_INLINE}"
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
        "--chunk-size",
        type=int,
        default=450,
        help="Chunk size in characters (default: 450, HTML is stripped first)"
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=50,
        help="Chunk overlap in characters (default: 50)"
    )
    parser.add_argument(
        "--min-chunk-length",
        type=int,
        default=50,
        help="Minimum chunk length to keep (default: 50, filters out HTML fragments)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=500,
        help="Max chunks per API call to avoid gRPC limits (default: 500)"
    )
    
    args = parser.parse_args()
    
    # Determine milvus mode from flags
    if args.remote:
        milvus_mode = MILVUS_MODE_REMOTE
    elif args.inline:
        milvus_mode = MILVUS_MODE_INLINE
    else:
        milvus_mode = args.milvus_mode
    
    print(f"🔗 Connecting to: {args.url}")
    print(f"📦 Milvus mode: {milvus_mode}")
    if not args.verify_ssl:
        print("⚠️  SSL verification disabled (default)")
    
    # Generate vector store name based on current directory
    vector_store_name = f"milvus_collection_{Path.cwd().name}"
    
    config = MilvusUploadConfig(
        llama_stack_url=args.url,
        documents_dir=args.documents_dir,
        embedding_model=args.embedding_model,
        vector_store_name=vector_store_name,
        milvus_mode=milvus_mode,
        verify_ssl=args.verify_ssl,
        timeout=args.timeout,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
        batch_size=args.batch_size,
        min_chunk_length=args.min_chunk_length,
    )
    
    try:
        vector_store_id = upload_documents_to_milvus(config)
        
        print(f"\n{'='*60}")
        print(f"📝 Next steps:")
        print(f"{'='*60}")
        print(f"Use this Vector Store ID in rag.py:")
        print(f"\nexport VECTOR_STORE_ID={vector_store_id}")
        print(f"python rag.py")
        print(f"{'='*60}\n")
        return 0
        
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        import traceback
        print("\n📋 Full traceback:", file=sys.stderr)
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
