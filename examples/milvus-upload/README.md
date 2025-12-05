# Milvus Upload Module

Reusable module for uploading documents to a Milvus vector store using Llama Stack.

## Usage as a Module

```python
import sys
sys.path.insert(0, "../milvus-upload")

from milvus_upload import MilvusUploadConfig, upload_documents_to_milvus

config = MilvusUploadConfig(
    llama_stack_url="https://llama-stack.example.com",
    documents_dir="./documents",
    embedding_model="granite-embedding-125m",
    vector_store_name="my-vector-store"
)

vector_store_id = upload_documents_to_milvus(config)
print(f"Vector Store ID: {vector_store_id}")
```

## Usage as CLI

```bash
# Basic usage
python cli.py --url https://llama-stack.example.com

# With custom documents directory
python cli.py --documents-dir ./my-docs

# With specific embedding model
python cli.py --embedding-model granite-embedding-125m

# All options
python cli.py \
    --url https://llama-stack.example.com \
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
| `provider_id` | str | `"inline-milvus"` | Milvus provider ID |
| `verify_ssl` | bool | `False` | Verify SSL certificates |
| `timeout` | int | `300` | Timeout in seconds |
| `verbose` | bool | `True` | Show logs |
