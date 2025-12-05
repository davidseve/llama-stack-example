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

from milvus_upload import MilvusUploadConfig, upload_documents_to_milvus, EMBEDDING_DIMENSIONS


def main():
    parser = argparse.ArgumentParser(
        description="Upload documents to Milvus using Llama Stack",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Available embedding models:
{chr(10).join(f'  - {model} ({dim} dim)' for model, dim in EMBEDDING_DIMENSIONS.items())}

⚠️ IMPORTANTE: El modelo de embedding DEBE coincidir con la configuración del servidor.
               El servidor está configurado con: granite-embedding-125m

Example:
  python milvus-upload.py --embedding-model granite-embedding-125m
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
        help="Embedding model to use (default: granite-embedding-125m, must match server config)"
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
    
    args = parser.parse_args()
    
    print(f"🔗 Connecting to: {args.url}")
    if not args.verify_ssl:
        print("⚠️  SSL verification disabled (default)")
    
    # Generate vector store name based on current directory
    vector_store_name = f"milvus_collection_{Path.cwd().name}"
    
    config = MilvusUploadConfig(
        llama_stack_url=args.url,
        documents_dir=args.documents_dir,
        embedding_model=args.embedding_model,
        vector_store_name=vector_store_name,
        verify_ssl=args.verify_ssl,
        timeout=args.timeout
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
