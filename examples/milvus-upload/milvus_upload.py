#!/usr/bin/env python3
"""
Milvus Upload Module for Llama Stack.

This module provides reusable functionality to upload documents to a Milvus 
vector store using Llama Stack's OpenAI-compatible API.

Two modes are supported:
1. Server-side chunking: Uses file upload + file_batches API (original approach)
2. Local chunking: Chunks documents locally and uses vector_io.insert (more control)
"""

import os
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List, Dict, Any
from openai import OpenAI
import httpx

# Optional import for local chunking with vector_io
try:
    from llama_stack_client import LlamaStackClient
    LLAMA_STACK_CLIENT_AVAILABLE = True
except ImportError:
    LLAMA_STACK_CLIENT_AVAILABLE = False


# =============================================================================
# CONSTANTS
# =============================================================================

# Common embedding dimensions for known models
EMBEDDING_DIMENSIONS = {
    "granite-embedding-125m": 768,
    "sentence-transformers/nomic-ai/nomic-embed-text-v1.5": 768,
    "nomic-embed-text-v1.5": 768,
    "all-MiniLM-L6-v2": 384,
    "multilingual-e5-large-vllm-embedding/multilingual-e5-large": 1024,
    "multilingual-e5-large": 1024,
}

# Milvus provider modes
MILVUS_MODE_INLINE = "inline"
MILVUS_MODE_REMOTE = "remote"

# Default provider IDs for each mode (as configured in Llama Stack)
MILVUS_PROVIDER_IDS = {
    MILVUS_MODE_INLINE: "milvus",      # provider_type: inline::milvus
    MILVUS_MODE_REMOTE: "milvus-remote",  # provider_type: remote::milvus
}

# Default chunking configuration
DEFAULT_CHUNK_SIZE = 1000  # characters
DEFAULT_CHUNK_OVERLAP = 200  # characters
DEFAULT_MAX_CHUNK_CHARS = 450  # Hard limit to avoid exceeding 512 tokens


# =============================================================================
# CONFIGURATION CLASSES
# =============================================================================

@dataclass
class MilvusUploadConfig:
    """Configuration for Milvus document upload (server-side chunking)."""
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


@dataclass
class MilvusLocalChunkingConfig:
    """Configuration for Milvus upload with LOCAL chunking."""
    llama_stack_url: str = field(default_factory=lambda: os.getenv("LLAMA_STACK_URL", "http://localhost:8321"))
    documents_dir: str = "documents"
    json_file: Optional[str] = None  # Alternative to documents_dir
    embedding_model: str = field(default_factory=lambda: os.getenv("EMBEDDING_MODEL", "granite-embedding-125m"))
    embedding_dimension: Optional[int] = None  # Auto-detect if None
    vector_store_name: Optional[str] = None  # Auto-generate if None
    # Chunking configuration
    chunk_size: int = DEFAULT_CHUNK_SIZE  # characters
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP  # characters
    max_chunk_chars: int = DEFAULT_MAX_CHUNK_CHARS  # hard limit
    # Insertion configuration
    batch_size: int = 1  # 1 = insert one by one (safer)
    # Milvus mode
    milvus_mode: str = field(default_factory=lambda: os.getenv("MILVUS_MODE", MILVUS_MODE_REMOTE))
    provider_id: Optional[str] = None
    # Connection
    verify_ssl: bool = False
    timeout: int = 300
    verbose: bool = True
    # Verification
    verify_query: Optional[str] = None  # Query to verify insertion
    
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


# =============================================================================
# TEXT CHUNKING
# =============================================================================

class TextChunker:
    """Text chunker with support for overlap."""
    
    def __init__(
        self,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
        separators: List[str] = None
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", ". ", " ", ""]
    
    def split_text(self, text: str) -> List[str]:
        """
        Split text into chunks respecting natural separators.
        
        Tries to split by paragraphs, then lines, then sentences,
        and finally by words if necessary.
        """
        chunks = self._split_text_recursive(text, self.separators)
        return self._merge_small_chunks(chunks)
    
    def _split_text_recursive(self, text: str, separators: List[str]) -> List[str]:
        """Recursively split using different separators."""
        if not text:
            return []
        
        # If text is smaller than chunk_size, return it
        if len(text) <= self.chunk_size:
            return [text.strip()] if text.strip() else []
        
        # Find the first separator that splits the text
        final_chunks = []
        separator = separators[-1]  # Default: character by character
        
        for sep in separators:
            if sep == "":
                separator = sep
                break
            if sep in text:
                separator = sep
                break
        
        # Split by separator
        splits = text.split(separator) if separator else list(text)
        
        current_chunk = []
        current_length = 0
        
        for split in splits:
            split_len = len(split) + len(separator)
            
            if current_length + split_len > self.chunk_size and current_chunk:
                # Save current chunk
                chunk_text = separator.join(current_chunk)
                if chunk_text.strip():
                    final_chunks.append(chunk_text.strip())
                
                # Overlap: keep part of previous chunk
                overlap_chunks = []
                overlap_length = 0
                for item in reversed(current_chunk):
                    if overlap_length + len(item) <= self.chunk_overlap:
                        overlap_chunks.insert(0, item)
                        overlap_length += len(item) + len(separator)
                    else:
                        break
                
                current_chunk = overlap_chunks
                current_length = overlap_length
            
            current_chunk.append(split)
            current_length += split_len
        
        # Last chunk
        if current_chunk:
            chunk_text = separator.join(current_chunk)
            if chunk_text.strip():
                final_chunks.append(chunk_text.strip())
        
        return final_chunks
    
    def _merge_small_chunks(self, chunks: List[str]) -> List[str]:
        """Merge very small chunks with the next one."""
        if not chunks:
            return []
        
        merged = []
        current = ""
        
        for chunk in chunks:
            if len(current) + len(chunk) <= self.chunk_size:
                current = f"{current}\n\n{chunk}".strip() if current else chunk
            else:
                if current:
                    merged.append(current)
                current = chunk
        
        if current:
            merged.append(current)
        
        return merged


def chunk_document(
    content: str,
    document_id: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    metadata: Dict[str, Any] = None,
    max_chunk_chars: int = DEFAULT_MAX_CHUNK_CHARS
) -> List[Dict[str, Any]]:
    """
    Split a document into chunks with metadata.
    
    Args:
        content: Document text content
        document_id: Unique identifier for the document
        chunk_size: Target chunk size in characters
        chunk_overlap: Overlap between chunks in characters
        metadata: Additional metadata to include in each chunk
        max_chunk_chars: Hard limit for chunk size (to avoid token limits)
    
    Returns:
        List of chunks with format for vector_io.insert
    """
    chunker = TextChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    text_chunks = chunker.split_text(content)
    
    chunks = []
    chunk_index = 0
    
    for chunk_text in text_chunks:
        # If chunk exceeds hard limit, split it
        if len(chunk_text) > max_chunk_chars:
            # Split into sub-chunks
            for j in range(0, len(chunk_text), max_chunk_chars - 50):
                sub_chunk = chunk_text[j:j + max_chunk_chars]
                if sub_chunk.strip():
                    chunk_metadata = {
                        "source": document_id,
                        "chunk_index": chunk_index,
                        "is_subchunk": True,
                        **(metadata or {})
                    }
                    chunks.append({
                        "chunk_id": f"{document_id}_chunk_{chunk_index}",
                        "content": sub_chunk.strip(),
                        "metadata": chunk_metadata
                    })
                    chunk_index += 1
        else:
            chunk_metadata = {
                "source": document_id,
                "chunk_index": chunk_index,
                **(metadata or {})
            }
            chunks.append({
                "chunk_id": f"{document_id}_chunk_{chunk_index}",
                "content": chunk_text,
                "metadata": chunk_metadata
            })
            chunk_index += 1
    
    # Update total_chunks in all chunks
    for chunk in chunks:
        chunk["metadata"]["total_chunks"] = len(chunks)
    
    return chunks


# =============================================================================
# DOCUMENT LOADING
# =============================================================================

def load_documents_from_directory(
    directory: Path,
    extensions: List[str] = None,
    verbose: bool = True
) -> List[Dict]:
    """
    Load documents from a directory.
    
    Args:
        directory: Path to directory containing documents
        extensions: List of file extensions to include (default: [".md", ".txt", ".rst"])
        verbose: Print progress messages
    
    Returns:
        List of document dicts with {document_id, content, metadata}
    """
    if extensions is None:
        extensions = [".md", ".txt", ".rst"]
    
    documents = []
    
    for ext in extensions:
        for file_path in sorted(Path(directory).glob(f"*{ext}")):
            try:
                content = file_path.read_text(encoding="utf-8")
                
                documents.append({
                    "document_id": file_path.name,
                    "content": content,
                    "metadata": {
                        "filename": file_path.name,
                        "file_path": str(file_path),
                        "file_size": file_path.stat().st_size,
                        "extension": ext,
                    }
                })
                
            except Exception as e:
                if verbose:
                    print(f"   ⚠️  Error reading {file_path}: {e}")
    
    return documents


def load_documents_from_json(json_path: Path) -> List[Dict]:
    """
    Load documents from a JSON file.
    
    Supports formats:
    - List of objects with {id/document_id, content/text, metadata}
    
    Args:
        json_path: Path to JSON file
    
    Returns:
        List of document dicts with {document_id, content, metadata}
    """
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    if isinstance(data, list):
        documents = []
        for i, item in enumerate(data):
            doc = {
                "document_id": item.get("id", item.get("document_id", f"doc_{i}")),
                "content": item.get("content", item.get("text", "")),
                "metadata": item.get("metadata", {})
            }
            documents.append(doc)
        return documents
    
    raise ValueError(f"Unsupported JSON format: {type(data)}")


# =============================================================================
# CLIENT CREATION
# =============================================================================

def create_clients(base_url: str, timeout: int = 300, verify_ssl: bool = False):
    """
    Create Llama Stack and OpenAI clients.
    
    Args:
        base_url: Llama Stack server URL
        timeout: Request timeout in seconds
        verify_ssl: Whether to verify SSL certificates
    
    Returns:
        Tuple of (LlamaStackClient, OpenAI client)
    """
    http_client = httpx.Client(verify=verify_ssl, timeout=timeout)
    
    if LLAMA_STACK_CLIENT_AVAILABLE:
        llama_client = LlamaStackClient(
            base_url=base_url,
            http_client=http_client
        )
    else:
        llama_client = None
    
    openai_client = OpenAI(
        base_url=f"{base_url}/v1",
        api_key="fake-key",
        http_client=http_client
    )
    
    return llama_client, openai_client


def create_vector_store(
    openai_client: OpenAI,
    name: str,
    embedding_model: str,
    embedding_dimension: int,
    provider_id: str = "milvus-remote",
    verbose: bool = True
) -> str:
    """
    Create a new vector store in Milvus.
    
    Args:
        openai_client: OpenAI-compatible client
        name: Name for the vector store
        embedding_model: Embedding model identifier
        embedding_dimension: Dimension of embeddings
        provider_id: Milvus provider ID
        verbose: Print progress messages
    
    Returns:
        Vector store ID
    """
    if verbose:
        print(f"\n🗄️  Creating vector store '{name}'...")
    
    vector_store = openai_client.vector_stores.create(
        name=name,
        extra_body={
            "embedding_model": embedding_model,
            "embedding_dimension": embedding_dimension,
            "provider_id": provider_id
        }
    )
    
    if verbose:
        print(f"   ✅ Vector Store ID: {vector_store.id}")
    
    return vector_store.id


# =============================================================================
# CHUNK INSERTION (LOCAL CHUNKING)
# =============================================================================

def insert_chunks_with_vector_io(
    llama_client,  # LlamaStackClient
    vector_store_id: str,
    chunks: List[Dict[str, Any]],
    batch_size: int = 1,
    verbose: bool = False
) -> int:
    """
    Insert pre-processed chunks using vector_io.insert.
    
    Args:
        llama_client: Llama Stack client
        vector_store_id: ID of the vector store
        chunks: List of chunks with format {chunk_id, content, metadata}
        batch_size: Batch size for insertion (1 = one by one, safer)
        verbose: Show detailed progress
        
    Returns:
        Number of chunks inserted
    """
    if not LLAMA_STACK_CLIENT_AVAILABLE:
        raise RuntimeError("llama_stack_client is required for local chunking. Install with: pip install llama-stack-client")
    
    total_inserted = 0
    total_failed = 0
    
    # Insert in batches (or one by one if batch_size=1)
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        
        # Format chunks for vector_io.insert
        formatted_chunks = []
        for chunk in batch:
            formatted_chunks.append({
                "content": chunk["content"],
                "metadata": {
                    "document_id": chunk.get("chunk_id", f"chunk_{i}"),
                    **chunk.get("metadata", {})
                }
            })
        
        try:
            llama_client.vector_io.insert(
                vector_db_id=vector_store_id,
                chunks=formatted_chunks
            )
            total_inserted += len(batch)
            
            if verbose or batch_size > 1:
                print(f"   ✅ Batch {i//batch_size + 1}: {len(batch)} chunks inserted")
            elif (i + 1) % 100 == 0 or i == len(chunks) - 1:
                print(f"   📊 Progress: {total_inserted}/{len(chunks)} inserted, {total_failed} errors")
            
        except Exception as e:
            total_failed += len(batch)
            if verbose:
                print(f"   ❌ Error in chunk {i}: {str(e)[:100]}...")
    
    print(f"   ✅ Total inserted: {total_inserted}")
    if total_failed > 0:
        print(f"   ⚠️  Total failed: {total_failed}")
    
    return total_inserted


def verify_insertion(
    llama_client,  # LlamaStackClient
    vector_store_id: str,
    query: str = "test",
    verbose: bool = True
) -> int:
    """
    Verify that chunks were inserted correctly.
    
    Args:
        llama_client: Llama Stack client
        vector_store_id: ID of the vector store
        query: Query to test retrieval
        verbose: Print progress messages
    
    Returns:
        Number of chunks retrieved
    """
    if verbose:
        print(f"\n🔍 Verifying insertion with query: '{query}'")
    
    try:
        results = llama_client.vector_io.query(
            vector_db_id=vector_store_id,
            query=query,
            params={"max_chunks": 5}
        )
        
        chunk_count = len(results.chunks) if hasattr(results, 'chunks') else 0
        
        if verbose:
            print(f"   ✅ Query returned {chunk_count} chunks")
            
            if chunk_count > 0 and hasattr(results, 'chunks'):
                print(f"\n   📋 Example retrieved chunk:")
                chunk = results.chunks[0]
                content = chunk.content[:200] if hasattr(chunk, 'content') else str(chunk)[:200]
                print(f"      {content}...")
        
        return chunk_count
        
    except Exception as e:
        if verbose:
            print(f"   ❌ Error verifying: {e}")
        return 0


# =============================================================================
# MAIN UPLOAD FUNCTIONS
# =============================================================================

def upload_documents_to_milvus(config: MilvusUploadConfig) -> str:
    """
    Upload documents from a folder to Milvus using Llama Stack.
    Uses SERVER-SIDE chunking via file upload + file_batches API.
    
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


def upload_documents_with_local_chunking(config: MilvusLocalChunkingConfig) -> Dict[str, Any]:
    """
    Upload documents to Milvus with LOCAL chunking.
    
    This function:
    1. Reads documents from directory or JSON file
    2. Chunks documents LOCALLY (doesn't depend on server)
    3. Creates a vector store in Milvus
    4. Inserts chunks using vector_io.insert
    5. Optionally verifies the insertion
    
    Advantages:
    - Full control over chunk size and overlap
    - Support for overlap between chunks
    - Doesn't depend on server's chunk_size_in_tokens parameter
    
    Args:
        config: MilvusLocalChunkingConfig with all settings
        
    Returns:
        Dict with upload results including vector_store_id, counts, etc.
    """
    def log(msg: str):
        if config.verbose:
            print(msg)
    
    # Banner
    log("=" * 70)
    log("📚 UPLOAD DOCUMENTS TO MILVUS WITH LOCAL CHUNKING")
    log("=" * 70)
    log(f"   URL: {config.llama_stack_url}")
    log(f"   Embedding Model: {config.embedding_model}")
    log(f"   Embedding Dimension: {config.embedding_dimension}")
    log(f"   Chunk Size: {config.chunk_size} characters")
    log(f"   Chunk Overlap: {config.chunk_overlap} characters")
    log(f"   Max Chunk Chars: {config.max_chunk_chars} (hard limit)")
    log(f"   Batch Size: {config.batch_size}")
    if not config.verify_ssl:
        log("   ⚠️  SSL verification disabled (default)")
    
    # Create clients
    llama_client, openai_client = create_clients(
        config.llama_stack_url,
        timeout=config.timeout,
        verify_ssl=config.verify_ssl
    )
    
    if llama_client is None:
        raise RuntimeError("llama_stack_client is required for local chunking. Install with: pip install llama-stack-client")
    
    # Load documents
    if config.json_file:
        log(f"\n📂 Loading from JSON: {config.json_file}")
        documents = load_documents_from_json(Path(config.json_file))
    else:
        log(f"\n📂 Loading from directory: {config.documents_dir}")
        docs_path = Path(config.documents_dir)
        if not docs_path.exists():
            raise FileNotFoundError(f"Directory does not exist: {config.documents_dir}")
        documents = load_documents_from_directory(docs_path, verbose=config.verbose)
    
    if not documents:
        raise ValueError("No documents found")
    
    log(f"   ✅ {len(documents)} documents loaded")
    
    # Perform LOCAL chunking
    log(f"\n✂️  Performing local chunking...")
    all_chunks = []
    for doc in documents:
        doc_chunks = chunk_document(
            content=doc["content"],
            document_id=doc["document_id"],
            chunk_size=config.chunk_size,
            chunk_overlap=config.chunk_overlap,
            metadata=doc.get("metadata", {}),
            max_chunk_chars=config.max_chunk_chars
        )
        log(f"   📄 {doc['document_id']}: {len(doc_chunks)} chunks")
        all_chunks.extend(doc_chunks)
    
    log(f"\n   📊 Total chunks generated: {len(all_chunks)}")
    
    # Show chunk statistics
    if all_chunks:
        chunk_sizes = [len(c["content"]) for c in all_chunks]
        log(f"   📏 Average size: {sum(chunk_sizes)//len(chunk_sizes)} characters")
        log(f"   📏 Min size: {min(chunk_sizes)} characters")
        log(f"   📏 Max size: {max(chunk_sizes)} characters")
    
    # Generate vector store name if not provided
    from datetime import datetime
    vector_store_name = config.vector_store_name or f"local_chunking_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Create vector store
    vector_store_id = create_vector_store(
        openai_client,
        vector_store_name,
        config.embedding_model,
        config.embedding_dimension,
        config.provider_id,
        verbose=config.verbose
    )
    
    # Insert chunks using vector_io
    log(f"\n📤 Inserting {len(all_chunks)} chunks...")
    inserted = insert_chunks_with_vector_io(
        llama_client,
        vector_store_id,
        all_chunks,
        batch_size=config.batch_size,
        verbose=config.verbose
    )
    
    # Verify if query provided
    if config.verify_query:
        verify_insertion(llama_client, vector_store_id, config.verify_query, verbose=config.verbose)
    
    # Summary
    log("\n" + "=" * 70)
    log("✅ COMPLETED")
    log("=" * 70)
    log(f"   Vector Store ID: {vector_store_id}")
    log(f"   Store Name: {vector_store_name}")
    log(f"   Documents: {len(documents)}")
    log(f"   Chunks inserted: {inserted}")
    log(f"   Chunk Size: {config.chunk_size} chars")
    log(f"   Chunk Overlap: {config.chunk_overlap} chars")
    
    return {
        "vector_store_id": vector_store_id,
        "store_name": vector_store_name,
        "documents_count": len(documents),
        "chunks_count": inserted,
        "chunk_size": config.chunk_size,
        "chunk_overlap": config.chunk_overlap,
        "embedding_model": config.embedding_model,
        "embedding_dimension": config.embedding_dimension,
    }


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

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
