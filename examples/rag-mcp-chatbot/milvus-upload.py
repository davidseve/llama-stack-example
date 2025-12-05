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

from milvus_upload import MilvusUploadConfig, upload_documents_to_milvus


def main():
    parser = argparse.ArgumentParser(
        description="Upload documents to Milvus using Llama Stack",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  python milvus-upload.py --url https://llama-stack.example.com
  python milvus-upload.py --documents-dir ./my-docs
        """
    )
    parser.add_argument(
        "--url",
        default=os.getenv("REMOTE_BASE_URL", "http://localhost:8321"),
        help="Llama Stack URL"
    )
    parser.add_argument(
        "--documents-dir",
        default="documents",
        help="Directory containing documents (default: documents)"
    )
    parser.add_argument(
        "--embedding-model",
        default=os.getenv("EMBEDDING_MODEL", "granite-embedding-125m"),
        help="Embedding model (default: granite-embedding-125m)"
    )
    parser.add_argument(
        "--vector-store-name",
        default="discounts-app-docs",
        help="Name for the vector store (default: discounts-app-docs)"
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
    
    args = parser.parse_args()
    
    print(f"🔗 Connecting to: {args.url}")
    if not args.verify_ssl:
        print("⚠️  SSL verification disabled")
    
    config = MilvusUploadConfig(
        llama_stack_url=args.url,
        documents_dir=args.documents_dir,
        embedding_model=args.embedding_model,
        vector_store_name=args.vector_store_name,
        verify_ssl=args.verify_ssl,
        timeout=args.timeout
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
