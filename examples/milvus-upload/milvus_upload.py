#!/usr/bin/env python3
"""
Milvus Upload Module for Llama Stack.

This module provides reusable functionality to upload documents to a Milvus 
vector store using Llama Stack's OpenAI-compatible API.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List
from openai import OpenAI
import httpx


# Common embedding dimensions for known models
EMBEDDING_DIMENSIONS = {
    "granite-embedding-125m": 768,
    "sentence-transformers/nomic-ai/nomic-embed-text-v1.5": 768,
    "nomic-embed-text-v1.5": 768,
    "all-MiniLM-L6-v2": 384,
}


@dataclass
class MilvusUploadConfig:
    """Configuration for Milvus document upload."""
    llama_stack_url: str = field(default_factory=lambda: os.getenv("REMOTE_BASE_URL", "http://localhost:8321"))
    documents_dir: str = "documents"
    embedding_model: str = field(default_factory=lambda: os.getenv("EMBEDDING_MODEL", "granite-embedding-125m"))
    embedding_dimension: Optional[int] = None  # Auto-detect if None
    vector_store_name: Optional[str] = None  # Auto-generate if None
    provider_id: str = "inline-milvus"
    verify_ssl: bool = False
    timeout: int = 300
    verbose: bool = True
    
    def __post_init__(self):
        # Auto-detect embedding dimension if not provided
        if self.embedding_dimension is None:
            self.embedding_dimension = EMBEDDING_DIMENSIONS.get(self.embedding_model, 768)


def upload_documents_to_milvus(config: MilvusUploadConfig) -> str:
    """
    Upload documents from a folder to Milvus using Llama Stack.
    
    Args:
        config: MilvusUploadConfig with all upload settings
        
    Returns:
        ID of the vector store created in Milvus
        
    Raises:
        FileNotFoundError: If documents directory doesn't exist
        ValueError: If no documents found or upload fails
    """
    def log(msg: str):
        if config.verbose:
            print(msg)
    
    # Initialize OpenAI-compatible client
    http_client = httpx.Client(verify=config.verify_ssl, timeout=config.timeout)
    client = OpenAI(
        base_url=f"{config.llama_stack_url}/v1",
        api_key="fake-api-key",  # Llama Stack doesn't require a real API key
        http_client=http_client
    )
    
    # Validate embedding model
    log(f"🔍 Checking embedding model '{config.embedding_model}'...")
    try:
        models = client.models.list()
        available_models = [m.identifier for m in models.data if hasattr(m, 'identifier')]
        embedding_models = [m for m in models.data if hasattr(m, 'model_type') and m.model_type == 'embedding']
        
        if config.embedding_model not in available_models:
            log(f"⚠️  WARNING: Embedding model '{config.embedding_model}' not found")
            if embedding_models:
                log("Available embedding models:")
                for model in embedding_models:
                    dim = model.metadata.get('embedding_dimension', 'unknown') if hasattr(model, 'metadata') else 'unknown'
                    log(f"  - {model.identifier} (dimension: {dim})")
                raise ValueError(f"Embedding model '{config.embedding_model}' not available. Use one of the models listed above.")
        else:
            # Find the model and print its details
            matching_model = next((m for m in embedding_models if m.identifier == config.embedding_model), None)
            if matching_model and hasattr(matching_model, 'metadata'):
                dim = matching_model.metadata.get('embedding_dimension', 'unknown')
                log(f"✓ Embedding model '{config.embedding_model}' is available (dimension: {dim})")
            else:
                log(f"✓ Embedding model '{config.embedding_model}' is available")
    except ValueError:
        raise  # Re-raise ValueError for model not found
    except Exception as e:
        log(f"⚠️  Could not verify embedding model: {e}")
        log("Proceeding anyway...")
    
    # Verify documents directory
    docs_path = Path(config.documents_dir)
    if not docs_path.exists():
        raise FileNotFoundError(f"Directory {config.documents_dir} does not exist")
    
    doc_files = [f for f in docs_path.glob("*") if f.is_file()]
    if not doc_files:
        raise ValueError(f"No documents found in {config.documents_dir}")
    
    log(f"📁 Found {len(doc_files)} documents in {config.documents_dir}")
    
    # Upload files
    log("\n📤 Uploading files...")
    file_ids = []
    for doc_file in doc_files:
        log(f"  - Uploading: {doc_file.name}")
        with open(doc_file, "rb") as f:
            file_obj = client.files.create(file=f, purpose="assistants")
            file_ids.append(file_obj.id)
            log(f"    ✓ File ID: {file_obj.id}")
    
    if not file_ids:
        raise ValueError("Could not upload any file")
    
    log(f"\n✓ {len(file_ids)} files uploaded successfully")
    
    # Create vector store
    log("\n🗄️  Creating Milvus vector store...")
    vector_store_name = config.vector_store_name or f"milvus_collection_{Path.cwd().name}"
    
    log(f"Using embedding model: {config.embedding_model}")
    log(f"Embedding dimension: {config.embedding_dimension}")
    
    vector_store = client.vector_stores.create(
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
    
    # Associate files to vector store
    log("\n🔗 Indexing documents...")
    client.vector_stores.file_batches.create_and_poll(
        vector_store_id=vector_store_id,
        file_ids=file_ids
    )
    
    log(f"✓ {len(file_ids)} documents indexed")
    log(f"\n{'='*60}")
    log(f"✅ UPLOAD COMPLETED")
    log(f"{'='*60}")
    log(f"Vector Store ID: {vector_store_id}")
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

