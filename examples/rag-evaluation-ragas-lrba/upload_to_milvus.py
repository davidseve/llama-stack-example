#!/usr/bin/env python3
"""
Script para subir documentos a Milvus via Llama Stack.

Este script:
1. Lee documentos desde un directorio
2. Crea un vector store en Milvus
3. Inserta los documentos (chunking automático en servidor)
4. Verifica que los chunks se insertaron correctamente

Configuración:
- Embedding Model: multilingual-e5-large-vllm-embedding/multilingual-e5-large
- Embedding Dimension: 476
- Vector DB Provider: milvus-remote
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

import httpx
from llama_stack_client import LlamaStackClient
from openai import OpenAI


# =============================================================================
# CONFIGURACIÓN
# =============================================================================

LLAMA_STACK_URL = os.environ.get(
    "LLAMA_STACK_URL",
    "https://llama-stack-ai2-llama-stack-ai2.apps.ai2-es-dev.pcore.work.eu-aws-02.nextgen.igrupobbva"
)

# Modelo de embedding (debe coincidir con el configurado en Llama Stack)
EMBEDDING_MODEL = "multilingual-e5-large-vllm-embedding/multilingual-e5-large"
EMBEDDING_DIMENSION = 476

# Configuración de chunking
DEFAULT_CHUNK_SIZE = 512  # tokens


# =============================================================================
# FUNCIONES
# =============================================================================

def create_clients(base_url: str, timeout: int = 300):
    """Crea los clientes de Llama Stack y OpenAI."""
    http_client = httpx.Client(verify=False, timeout=timeout)
    
    llama_client = LlamaStackClient(
        base_url=base_url,
        http_client=http_client
    )
    
    openai_client = OpenAI(
        base_url=f"{base_url}/v1",
        api_key="fake-key",
        http_client=http_client
    )
    
    return llama_client, openai_client


def create_vector_store(openai_client: OpenAI, name: str) -> str:
    """Crea un nuevo vector store en Milvus."""
    print(f"\n🗄️  Creando vector store '{name}'...")
    
    vector_store = openai_client.vector_stores.create(
        name=name,
        extra_body={
            "embedding_model": EMBEDDING_MODEL,
            "embedding_dimension": EMBEDDING_DIMENSION,
            "provider_id": "milvus-remote"
        }
    )
    
    print(f"   ✅ Vector Store ID: {vector_store.id}")
    return vector_store.id


def load_documents_from_directory(directory: Path, extensions: list = None) -> list:
    """Carga documentos desde un directorio."""
    if extensions is None:
        extensions = [".md", ".txt", ".rst"]
    
    documents = []
    
    for ext in extensions:
        for file_path in sorted(directory.glob(f"*{ext}")):
            try:
                content = file_path.read_text(encoding="utf-8")
                
                # Determinar mime_type
                mime_type = "text/plain"
                if ext == ".md":
                    mime_type = "text/markdown"
                
                documents.append({
                    "document_id": file_path.name,
                    "content": content,
                    "mime_type": mime_type,
                    "metadata": {
                        "source": file_path.name,
                        "filename": file_path.name,
                        "file_path": str(file_path),
                        "file_size": file_path.stat().st_size,
                        "extension": ext,
                    }
                })
                
            except Exception as e:
                print(f"   ⚠️  Error leyendo {file_path}: {e}")
    
    return documents


def load_documents_from_json(json_path: Path) -> list:
    """Carga documentos/chunks desde un archivo JSON."""
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Si es una lista, asumimos que son chunks
    if isinstance(data, list):
        documents = []
        for i, item in enumerate(data):
            doc = {
                "document_id": item.get("id", item.get("document_id", f"chunk_{i}")),
                "content": item.get("content", item.get("text", "")),
                "mime_type": item.get("mime_type", "text/plain"),
                "metadata": item.get("metadata", {})
            }
            
            # Agregar campos adicionales a metadata
            for key in ["source", "filename", "chunk_index", "total_chunks"]:
                if key in item and key not in doc["metadata"]:
                    doc["metadata"][key] = item[key]
            
            documents.append(doc)
        
        return documents
    
    raise ValueError(f"Formato de JSON no soportado: {type(data)}")


def insert_documents(
    llama_client: LlamaStackClient,
    vector_store_id: str,
    documents: list,
    chunk_size: int = DEFAULT_CHUNK_SIZE
) -> None:
    """Inserta documentos en el vector store usando rag_tool.insert."""
    print(f"\n📤 Insertando {len(documents)} documentos...")
    
    # Mostrar documentos a insertar
    for doc in documents:
        size = len(doc["content"])
        print(f"   📄 {doc['document_id']} ({size:,} chars)")
    
    # Insertar usando rag_tool (chunking automático en servidor)
    result = llama_client.tool_runtime.rag_tool.insert(
        documents=documents,
        vector_db_id=vector_store_id,
        chunk_size_in_tokens=chunk_size,
    )
    
    print(f"\n   ✅ Documentos insertados correctamente")
    return result


def verify_insertion(
    llama_client: LlamaStackClient,
    vector_store_id: str,
    query: str = "test"
) -> int:
    """Verifica que los documentos se insertaron correctamente."""
    print(f"\n🔍 Verificando inserción...")
    
    try:
        results = llama_client.vector_io.query(
            vector_db_id=vector_store_id,
            query=query,
            params={"max_chunks": 5}
        )
        
        chunk_count = len(results.chunks) if hasattr(results, 'chunks') else 0
        print(f"   ✅ Query de prueba devolvió {chunk_count} chunks")
        
        if chunk_count > 0 and hasattr(results, 'chunks'):
            print(f"\n   📋 Ejemplo de chunk recuperado:")
            chunk = results.chunks[0]
            content = chunk.content[:200] if hasattr(chunk, 'content') else str(chunk)[:200]
            print(f"      {content}...")
        
        return chunk_count
        
    except Exception as e:
        print(f"   ❌ Error verificando: {e}")
        return 0


def main():
    parser = argparse.ArgumentParser(
        description="Sube documentos a Milvus via Llama Stack"
    )
    
    parser.add_argument(
        "--documents-dir",
        type=Path,
        default=Path("documents"),
        help="Directorio con documentos a cargar (default: documents)"
    )
    
    parser.add_argument(
        "--json-file",
        type=Path,
        help="Archivo JSON con documentos/chunks (alternativa a --documents-dir)"
    )
    
    parser.add_argument(
        "--store-name",
        type=str,
        default=f"lrba_docs_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        help="Nombre del vector store a crear"
    )
    
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=DEFAULT_CHUNK_SIZE,
        help=f"Tamaño de chunk en tokens (default: {DEFAULT_CHUNK_SIZE})"
    )
    
    parser.add_argument(
        "--llama-stack-url",
        type=str,
        default=LLAMA_STACK_URL,
        help="URL del servidor Llama Stack"
    )
    
    parser.add_argument(
        "--verify-query",
        type=str,
        default="LRBA",
        help="Query para verificar inserción (default: LRBA)"
    )
    
    args = parser.parse_args()
    
    # Banner
    print("=" * 60)
    print("📚 UPLOAD DOCUMENTOS A MILVUS VIA LLAMA STACK")
    print("=" * 60)
    print(f"   URL: {args.llama_stack_url}")
    print(f"   Embedding Model: {EMBEDDING_MODEL}")
    print(f"   Embedding Dimension: {EMBEDDING_DIMENSION}")
    print(f"   Chunk Size: {args.chunk_size} tokens")
    
    # Crear clientes
    llama_client, openai_client = create_clients(args.llama_stack_url)
    
    # Cargar documentos
    if args.json_file:
        print(f"\n📂 Cargando desde JSON: {args.json_file}")
        documents = load_documents_from_json(args.json_file)
    else:
        print(f"\n📂 Cargando desde directorio: {args.documents_dir}")
        if not args.documents_dir.exists():
            print(f"   ❌ Directorio no existe: {args.documents_dir}")
            sys.exit(1)
        documents = load_documents_from_directory(args.documents_dir)
    
    if not documents:
        print("   ❌ No se encontraron documentos")
        sys.exit(1)
    
    print(f"   ✅ {len(documents)} documentos cargados")
    
    # Crear vector store
    vector_store_id = create_vector_store(openai_client, args.store_name)
    
    # Insertar documentos
    insert_documents(
        llama_client,
        vector_store_id,
        documents,
        chunk_size=args.chunk_size
    )
    
    # Verificar
    verify_insertion(llama_client, vector_store_id, args.verify_query)
    
    # Resumen final
    print("\n" + "=" * 60)
    print("✅ COMPLETADO")
    print("=" * 60)
    print(f"   Vector Store ID: {vector_store_id}")
    print(f"   Store Name: {args.store_name}")
    print(f"   Documentos: {len(documents)}")
    print()
    print("   Para usar con file_search:")
    print(f'   curl -k -X POST "{args.llama_stack_url}/v1/responses" \\')
    print('     -H "Content-Type: application/json" \\')
    print('     -d \'{')
    print('       "input": "tu pregunta aquí",')
    print('       "model": "llama-4-scout-17b-16e-w4a16-vllm-inference/RedHatAI/Llama-4-Scout-17B-16E-Instruct-quantized.w4a16",')
    print('       "tools": [{"type": "file_search", "vector_store_ids": ["' + vector_store_id + '"]}]')
    print("     }'")
    print()


if __name__ == "__main__":
    main()

