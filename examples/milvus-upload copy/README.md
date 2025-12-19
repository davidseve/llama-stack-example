# Milvus Upload Module

Reusable module for uploading documents to a Milvus vector store using Llama Stack.

## Milvus Modes

This module supports two Milvus deployment modes:

| Mode | Description | Provider ID |
|------|-------------|-------------|
| `inline` | Embedded/local Milvus database | `milvus` |
| `remote` | External Milvus server | `milvus-remote` |

## Usage as a Module

```python
import sys
sys.path.insert(0, "../milvus-upload")

from milvus_upload import (
    MilvusUploadConfig, 
    upload_documents_to_milvus,
    MILVUS_MODE_INLINE,
    MILVUS_MODE_REMOTE
)

# Use inline (embedded) Milvus - default
config = MilvusUploadConfig(
    llama_stack_url="https://llama-stack.example.com",
    documents_dir="./documents",
    embedding_model="granite-embedding-125m",
    vector_store_name="my-vector-store",
    milvus_mode=MILVUS_MODE_INLINE  # or just "inline"
)

# Use remote Milvus server
config_remote = MilvusUploadConfig(
    llama_stack_url="https://llama-stack.example.com",
    documents_dir="./documents",
    embedding_model="granite-embedding-125m",
    vector_store_name="my-vector-store",
    milvus_mode=MILVUS_MODE_REMOTE  # or just "remote"
)

vector_store_id = upload_documents_to_milvus(config)
print(f"Vector Store ID: {vector_store_id}")
```

## Usage as CLI

```bash
# Use inline (embedded) Milvus - default
python cli.py --url https://llama-stack.example.com

# Use remote Milvus server (long form)
python cli.py --milvus-mode remote --url https://llama-stack.example.com

# Use remote Milvus server (shorthand)
python cli.py --remote --url https://llama-stack.example.com

# Explicitly use inline (shorthand)
python cli.py --inline --url https://llama-stack.example.com

# With custom documents directory
python cli.py --documents-dir ./my-docs

# With specific embedding model
python cli.py --embedding-model granite-embedding-125m

# All options with remote Milvus
python cli.py \
    --url https://llama-stack.example.com \
    --remote \
    --documents-dir ./documents \
    --embedding-model granite-embedding-125m \
    --vector-store-name my-collection \
    --timeout 600
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `REMOTE_BASE_URL` | Llama Stack URL | `http://localhost:8321` |
| `EMBEDDING_MODEL` | Embedding model | `granite-embedding-125m` |
| `MILVUS_MODE` | Milvus mode: `inline` or `remote` | `inline` |

## Available Embedding Models

| Model | Dimension |
|-------|-----------|
| `granite-embedding-125m` | 768 |
| `sentence-transformers/nomic-ai/nomic-embed-text-v1.5` | 768 |
| `all-MiniLM-L6-v2` | 384 |

## Configuration

The `MilvusUploadConfig` class accepts the following parameters:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `llama_stack_url` | str | `$REMOTE_BASE_URL` | Llama Stack server URL |
| `documents_dir` | str | `"documents"` | Directory with documents |
| `embedding_model` | str | `$EMBEDDING_MODEL` | Embedding model |
| `embedding_dimension` | int | Auto-detect | Embedding dimension |
| `vector_store_name` | str | Auto-generate | Vector store name |
| `milvus_mode` | str | `"inline"` | Milvus mode: `inline` or `remote` |
| `provider_id` | str | Auto-set | Milvus provider ID (auto-set from mode) |
| `verify_ssl` | bool | `False` | Verify SSL certificates |
| `timeout` | int | `300` | Timeout in seconds |
| `verbose` | bool | `True` | Show logs |
