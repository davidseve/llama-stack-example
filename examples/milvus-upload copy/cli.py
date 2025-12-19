#!/usr/bin/env python3
"""
CLI for uploading documents to Milvus using Llama Stack.

This script can be run directly or imported from other scripts.
"""

import os
import sys
import argparse

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
Available embedding models and dimensions:
{chr(10).join(f'  - {model}: {dim} dim' for model, dim in EMBEDDING_DIMENSIONS.items())}

Milvus modes:
  - inline: Use embedded/local Milvus (provider: {MILVUS_PROVIDER_IDS[MILVUS_MODE_INLINE]})
  - remote: Use external Milvus server (provider: {MILVUS_PROVIDER_IDS[MILVUS_MODE_REMOTE]})

Environment variables:
  REMOTE_BASE_URL    - Llama Stack URL (default: http://localhost:8321)
  EMBEDDING_MODEL    - Embedding model (default: granite-embedding-125m)
  MILVUS_MODE        - Milvus mode: inline or remote (default: inline)

Examples:
  # Use inline (embedded) Milvus (default)
  python cli.py --url https://llama-stack.example.com
  
  # Use remote Milvus server
  python cli.py --milvus-mode remote --url https://llama-stack.example.com
  
  # Use shorthand for remote
  python cli.py --remote --url https://llama-stack.example.com
  
  # Custom documents directory
  python cli.py --documents-dir ./my-docs --milvus-mode inline
        """
    )
    parser.add_argument(
        "--url",
        default=os.getenv("REMOTE_BASE_URL", "http://localhost:8321"),
        help="Llama Stack URL (default: from REMOTE_BASE_URL env or http://localhost:8321)"
    )
    parser.add_argument(
        "--documents-dir",
        default="documents",
        help="Directory containing documents (default: documents)"
    )
    parser.add_argument(
        "--embedding-model",
        default=os.getenv("EMBEDDING_MODEL", "granite-embedding-125m"),
        help="Embedding model (default: from EMBEDDING_MODEL env or granite-embedding-125m)"
    )
    parser.add_argument(
        "--embedding-dimension",
        type=int,
        default=None,
        help="Embedding dimension (default: auto-detect from model)"
    )
    parser.add_argument(
        "--vector-store-name",
        default=None,
        help="Name for the vector store (default: auto-generated)"
    )
    # Milvus mode selection
    milvus_group = parser.add_mutually_exclusive_group()
    milvus_group.add_argument(
        "--milvus-mode",
        choices=[MILVUS_MODE_INLINE, MILVUS_MODE_REMOTE],
        default=os.getenv("MILVUS_MODE", MILVUS_MODE_INLINE),
        help=f"Milvus mode: '{MILVUS_MODE_INLINE}' for embedded or '{MILVUS_MODE_REMOTE}' for external server (default: from MILVUS_MODE env or {MILVUS_MODE_INLINE})"
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
        "--provider-id",
        default=None,
        help="Custom Milvus provider ID (default: auto-set based on milvus-mode)"
    )
    parser.add_argument(
        "--verify-ssl",
        action="store_true",
        help="Enable SSL certificate verification"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Timeout in seconds (default: 300)"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress verbose output"
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
        print("⚠️  SSL verification disabled")
    
    config = MilvusUploadConfig(
        llama_stack_url=args.url,
        documents_dir=args.documents_dir,
        embedding_model=args.embedding_model,
        embedding_dimension=args.embedding_dimension,
        vector_store_name=args.vector_store_name,
        milvus_mode=milvus_mode,
        provider_id=args.provider_id,
        verify_ssl=args.verify_ssl,
        timeout=args.timeout,
        verbose=not args.quiet
    )
    
    try:
        vector_store_id = upload_documents_to_milvus(config)
        
        print(f"\n📝 Add this to your .env file:")
        print(f"VECTOR_STORE_ID={vector_store_id}")
        return 0
        
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

