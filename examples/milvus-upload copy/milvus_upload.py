#!/usr/bin/env python3
"""
Milvus Upload Module for Llama Stack.

This module provides functionality to upload documents to a Milvus vector store
using Llama Stack's vector_io.insert API with client-side chunking.

NOTE: The file_batches API ignores chunking_strategy. To control chunk size,
we pre-chunk documents locally and use vector_io.insert directly.

IMPORTANT: For multilingual embedding models, 1 token ≈ 2-3 characters.
           For 512-token models, use ~400-500 characters (after HTML cleanup).
"""

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List
from openai import OpenAI
import httpx

# Try to import Llama Stack client for vector_io API
try:
    from llama_stack_client import LlamaStackClient
    LLAMA_STACK_CLIENT_AVAILABLE = True
except ImportError:
    LLAMA_STACK_CLIENT_AVAILABLE = False

# Try to import text splitter for chunking
try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    TEXT_SPLITTER_AVAILABLE = True
except ImportError:
    TEXT_SPLITTER_AVAILABLE = False


# Common embedding dimensions for known models
EMBEDDING_DIMENSIONS = {
    "granite-embedding-125m": 768,
    "sentence-transformers/nomic-ai/nomic-embed-text-v1.5": 768,
    "nomic-embed-text-v1.5": 768,
    "all-MiniLM-L6-v2": 384,
    "multilingual-e5-large-vllm-embedding/multilingual-e5-large": 1024,
}

# Milvus provider modes
MILVUS_MODE_INLINE = "inline"
MILVUS_MODE_REMOTE = "remote"

# Default provider IDs for each mode (as configured in Llama Stack)
MILVUS_PROVIDER_IDS = {
    MILVUS_MODE_INLINE: "milvus",      # provider_type: inline::milvus
    MILVUS_MODE_REMOTE: "milvus-remote",  # provider_type: remote::milvus
}


@dataclass
class MilvusUploadConfig:
    """Configuration for Milvus document upload."""
    llama_stack_url: str = field(default_factory=lambda: os.getenv("REMOTE_BASE_URL", "http://localhost:8321"))
    documents_dir: str = "documents"
    embedding_model: str = field(default_factory=lambda: os.getenv("EMBEDDING_MODEL", "granite-embedding-125m"))
    embedding_dimension: Optional[int] = None  # Auto-detect if None
    vector_store_name: Optional[str] = None  # Auto-generate if None
    # Milvus mode: "inline" (embedded/local) or "remote" (external Milvus server)
    milvus_mode: str = field(default_factory=lambda: os.getenv("MILVUS_MODE", MILVUS_MODE_INLINE))
    provider_id: Optional[str] = None  # Auto-set based on milvus_mode if None
    verify_ssl: bool = False
    timeout: int = 300
    verbose: bool = True
    # Chunking configuration - client-side chunking to control chunk size
    # IMPORTANT: For multilingual models, 1 token ≈ 2-3 characters!
    # For 512-token limit: use ~400-500 chars after HTML stripping
    chunk_size: int = 450  # Good balance for 512-token multilingual models
    chunk_overlap: int = 50  # Overlap between chunks for context
    # Batch size for uploading chunks (to avoid gRPC message size limits)
    batch_size: int = 500  # Max chunks per API call
    # Minimum chunk length to filter out useless fragments (HTML tags, etc.)
    min_chunk_length: int = 20  # Skip chunks shorter than this
    
    def __post_init__(self):
        # Auto-detect embedding dimension if not provided
        if self.embedding_dimension is None:
            self.embedding_dimension = EMBEDDING_DIMENSIONS.get(self.embedding_model, 768)
        
        # Validate milvus_mode
        if self.milvus_mode not in (MILVUS_MODE_INLINE, MILVUS_MODE_REMOTE):
            raise ValueError(f"Invalid milvus_mode '{self.milvus_mode}'. Use '{MILVUS_MODE_INLINE}' or '{MILVUS_MODE_REMOTE}'")
        
        # Auto-set provider_id based on milvus_mode if not explicitly provided
        if self.provider_id is None:
            self.provider_id = MILVUS_PROVIDER_IDS[self.milvus_mode]


def upload_documents_to_milvus(config: MilvusUploadConfig) -> str:
    """
    Upload documents to Milvus using vector_io.insert API with client-side chunking.
    
    This bypasses the file_batches API which ignores chunking_strategy.
    Documents are chunked locally and inserted directly via vector_io.insert.
    
    Args:
        config: MilvusUploadConfig with all upload settings
        
    Returns:
        ID of the vector store created in Milvus
        
    Raises:
        ImportError: If required dependencies are not installed
        FileNotFoundError: If documents directory doesn't exist
        ValueError: If no documents found or upload fails
    """
    def log(msg: str):
        if config.verbose:
            print(msg)
    
    # Check dependencies
    if not LLAMA_STACK_CLIENT_AVAILABLE:
        raise ImportError(
            "llama-stack-client is required. Install with: pip install llama-stack-client"
        )
    
    if not TEXT_SPLITTER_AVAILABLE:
        raise ImportError(
            "langchain-text-splitters is required for chunking. "
            "Install with: pip install langchain-text-splitters"
        )
    
    # Create shared httpx client with SSL settings
    http_client = httpx.Client(verify=config.verify_ssl, timeout=config.timeout)
    
    # Initialize Llama Stack client with custom httpx client for SSL
    log(f"🔗 Connecting to Llama Stack at {config.llama_stack_url}...")
    llama_client = LlamaStackClient(
        base_url=config.llama_stack_url,
        timeout=config.timeout,
        http_client=http_client,
    )
    
    # Also init OpenAI client for model validation and vector store creation
    openai_client = OpenAI(
        base_url=f"{config.llama_stack_url}/v1",
        api_key="fake-api-key",
        http_client=http_client
    )
    
    # Validate embedding model
    log(f"🔍 Checking embedding model '{config.embedding_model}'...")
    try:
        models = openai_client.models.list()
        available_models = [m.identifier for m in models.data if hasattr(m, 'identifier')]
        embedding_models = [m for m in models.data if hasattr(m, 'model_type') and m.model_type == 'embedding']
        
        if config.embedding_model not in available_models:
            log(f"⚠️  WARNING: Embedding model '{config.embedding_model}' not found")
            if embedding_models:
                log("Available embedding models:")
                for model in embedding_models:
                    dim = model.metadata.get('embedding_dimension', 'unknown') if hasattr(model, 'metadata') else 'unknown'
                    log(f"  - {model.identifier} (dimension: {dim})")
                raise ValueError(f"Embedding model '{config.embedding_model}' not available.")
        else:
            matching_model = next((m for m in embedding_models if m.identifier == config.embedding_model), None)
            if matching_model and hasattr(matching_model, 'metadata'):
                dim = matching_model.metadata.get('embedding_dimension', 'unknown')
                log(f"✓ Embedding model '{config.embedding_model}' is available (dimension: {dim})")
            else:
                log(f"✓ Embedding model '{config.embedding_model}' is available")
    except ValueError:
        raise
    except Exception as e:
        log(f"⚠️  Could not verify embedding model: {e}")
    
    # Verify documents directory
    docs_path = Path(config.documents_dir)
    if not docs_path.exists():
        raise FileNotFoundError(f"Directory {config.documents_dir} does not exist")
    
    doc_files = [f for f in docs_path.glob("*") if f.is_file()]
    if not doc_files:
        raise ValueError(f"No documents found in {config.documents_dir}")
    
    log(f"📁 Found {len(doc_files)} documents in {config.documents_dir}")
    
    # Initialize text splitter for client-side chunking
    log(f"\n✂️  Chunking configuration:")
    log(f"   Chunk size: {config.chunk_size} characters (~{config.chunk_size // 3}-{config.chunk_size // 2} tokens)")
    log(f"   Chunk overlap: {config.chunk_overlap} characters")
    log(f"   ℹ️  For 512-token models, 450 chars is a good default")
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.chunk_size,
        chunk_overlap=config.chunk_overlap,
        length_function=len,
        is_separator_regex=False,
    )
    
    # Create/get vector store using OpenAI API
    log("\n🗄️  Creating Milvus vector store...")
    vector_store_name = config.vector_store_name or f"milvus_collection_{Path.cwd().name}"
    
    vector_store = openai_client.vector_stores.create(
        name=vector_store_name,
        extra_body={
            "embedding_model": config.embedding_model,
            "embedding_dimension": config.embedding_dimension,
            "provider_id": config.provider_id
        }
    )
    
    vector_store_id = vector_store.id
    log(f"✓ Vector store created: {vector_store_name}")
    log(f"✓ Vector Store ID: {vector_store_id}")
    
    # Process and upload documents
    log("\n📤 Processing and uploading documents...")
    total_chunks = 0
    success_count = 0
    failed_count = 0
    
    for doc_file in doc_files:
        log(f"  - Processing: {doc_file.name}")
        
        # Read document content
        try:
            content = doc_file.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            try:
                content = doc_file.read_text(encoding='latin-1')
            except:
                log(f"    ⚠️  Could not read {doc_file.name}, skipping")
                failed_count += 1
                continue
        
        if not content.strip():
            log(f"    ⚠️  Empty file, skipping")
            failed_count += 1
            continue
        
        # Split into chunks
        text_chunks = splitter.split_text(content)
        
        # Filter out small/useless chunks
        filtered_chunks = []
        for chunk in text_chunks:
            chunk_clean = chunk.strip()
            # Skip chunks that are too short or just whitespace/punctuation
            if len(chunk_clean) >= config.min_chunk_length and re.search(r'[a-zA-Z]{3,}', chunk_clean):
                filtered_chunks.append(chunk_clean)
        
        skipped = len(text_chunks) - len(filtered_chunks)
        if skipped > 0:
            log(f"    → Split into {len(text_chunks)} chunks, filtered {skipped} small/empty")
        else:
            log(f"    → Split into {len(filtered_chunks)} chunks")
        
        if not filtered_chunks:
            log(f"    ⚠️  No valid chunks after filtering, skipping")
            failed_count += 1
            continue
        
        # Format chunks for vector_io.insert
        formatted_chunks = []
        for i, chunk_content in enumerate(filtered_chunks):
            formatted_chunks.append({
                "content": chunk_content,
                "mime_type": "text/plain",
                "metadata": {
                    "source": doc_file.name,
                    "chunk_index": i,
                    "total_chunks": len(filtered_chunks)
                }
            })
        
        # Upload chunks via vector_io.insert in batches
        try:
            # Split into batches to avoid gRPC message size limits
            num_batches = (len(formatted_chunks) + config.batch_size - 1) // config.batch_size
            if num_batches > 1:
                log(f"    → Uploading in {num_batches} batches...")
            
            for batch_idx in range(num_batches):
                start_idx = batch_idx * config.batch_size
                end_idx = min(start_idx + config.batch_size, len(formatted_chunks))
                batch = formatted_chunks[start_idx:end_idx]
                
                llama_client.vector_io.insert(
                    vector_db_id=vector_store_id,
                    chunks=batch
                )
                
                if num_batches > 1:
                    log(f"      ✓ Batch {batch_idx + 1}/{num_batches} ({len(batch)} chunks)")
            
            log(f"    ✓ Uploaded {len(filtered_chunks)} chunks")
            total_chunks += len(filtered_chunks)
            success_count += 1
        except Exception as e:
            error_msg = str(e)
            if "Connection error" in error_msg or "connection" in error_msg.lower():
                log(f"    ❌ Connection error - vector_io.insert API may not be available")
                log(f"       Try using --chunk-size 200 with file_batches API instead")
            elif "512 tokens" in error_msg or "context length" in error_msg.lower():
                log(f"    ❌ Token limit exceeded - reduce --chunk-size (current: {config.chunk_size})")
            elif "RESOURCE_EXHAUSTED" in error_msg or "message larger than max" in error_msg:
                log(f"    ❌ Message too large - reduce --batch-size (current: {config.batch_size})")
            else:
                log(f"    ❌ Failed to upload: {e}")
            failed_count += 1
    
    # Summary
    log(f"\n📊 Upload Summary:")
    log(f"   Documents: {success_count}/{len(doc_files)} succeeded")
    log(f"   Total chunks: {total_chunks}")
    
    if failed_count > 0:
        log(f"\n⚠️  {failed_count} documents failed. Tips:")
        log(f"   - Reduce chunk_size (e.g., --chunk-size 150)")
        log(f"   - For multilingual models: 1 token ≈ 2-3 chars")
    
    log(f"\n{'='*60}")
    log(f"✅ UPLOAD COMPLETED")
    log(f"{'='*60}")
    log(f"Vector Store ID: {vector_store_id}")
    log(f"Chunk size: {config.chunk_size} chars")
    log(f"{'='*60}\n")
    
    return vector_store_id


def get_available_embedding_models(
    llama_stack_url: str,
    verify_ssl: bool = False,
    timeout: int = 30
) -> List[dict]:
    """
    Get list of available embedding models from Llama Stack.
    
    Args:
        llama_stack_url: Base URL of Llama Stack
        verify_ssl: Whether to verify SSL certificates
        timeout: Timeout in seconds
        
    Returns:
        List of dicts with model info (identifier, dimension)
    """
    http_client = httpx.Client(verify=verify_ssl, timeout=timeout)
    client = OpenAI(
        base_url=f"{llama_stack_url}/v1",
        api_key="fake-api-key",
        http_client=http_client
    )
    
    models = client.models.list()
    embedding_models = []
    
    for model in models.data:
        if hasattr(model, 'model_type') and model.model_type == 'embedding':
            info = {
                "identifier": model.identifier,
                "dimension": model.metadata.get('embedding_dimension', 'unknown') if hasattr(model, 'metadata') else 'unknown'
            }
            embedding_models.append(info)
    
    return embedding_models
