#!/usr/bin/env python3
"""
Script para subir documentos a Milvus con chunking LOCAL.

Este script:
1. Lee documentos desde un directorio
2. Hace chunking LOCALMENTE (no depende del servidor)
3. Crea un vector store en Milvus
4. Inserta los chunks usando vector_io.insert
5. Verifica que los chunks se insertaron correctamente

Ventajas:
- Control total sobre el tamaño de chunks
- Soporte para overlap entre chunks
- No depende del parámetro chunk_size_in_tokens del servidor
"""

import os
import sys
import json
import argparse
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

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
EMBEDDING_MODEL = os.environ.get(
    "EMBEDDING_MODEL",
    "multilingual-e5-large-vllm-embedding/multilingual-e5-large"
)
EMBEDDING_DIMENSION = int(os.environ.get("EMBEDDING_DIMENSION", "476"))

# Configuración de chunking por defecto
DEFAULT_CHUNK_SIZE = 1000  # caracteres
DEFAULT_CHUNK_OVERLAP = 200  # caracteres


# =============================================================================
# CHUNKING LOCAL
# =============================================================================

class TextChunker:
    """Chunker de texto con soporte para overlap."""
    
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
        Divide el texto en chunks respetando separadores naturales.
        
        Intenta dividir por párrafos, luego por líneas, luego por oraciones,
        y finalmente por palabras si es necesario.
        """
        chunks = self._split_text_recursive(text, self.separators)
        return self._merge_small_chunks(chunks)
    
    def _split_text_recursive(self, text: str, separators: List[str]) -> List[str]:
        """Divide recursivamente usando diferentes separadores."""
        if not text:
            return []
        
        # Si el texto es menor que chunk_size, retornarlo
        if len(text) <= self.chunk_size:
            return [text.strip()] if text.strip() else []
        
        # Buscar el primer separador que divida el texto
        final_chunks = []
        separator = separators[-1]  # Default: caracter por caracter
        
        for sep in separators:
            if sep == "":
                separator = sep
                break
            if sep in text:
                separator = sep
                break
        
        # Dividir por el separador
        splits = text.split(separator) if separator else list(text)
        
        current_chunk = []
        current_length = 0
        
        for split in splits:
            split_len = len(split) + len(separator)
            
            if current_length + split_len > self.chunk_size and current_chunk:
                # Guardar chunk actual
                chunk_text = separator.join(current_chunk)
                if chunk_text.strip():
                    final_chunks.append(chunk_text.strip())
                
                # Overlap: mantener parte del chunk anterior
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
        
        # Último chunk
        if current_chunk:
            chunk_text = separator.join(current_chunk)
            if chunk_text.strip():
                final_chunks.append(chunk_text.strip())
        
        return final_chunks
    
    def _merge_small_chunks(self, chunks: List[str]) -> List[str]:
        """Combina chunks muy pequeños con el siguiente."""
        if not chunks:
            return []
        
        min_chunk_size = self.chunk_size // 4
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
    chunk_size: int,
    chunk_overlap: int,
    metadata: Dict[str, Any] = None,
    max_chunk_chars: int = 450  # Hard limit para evitar exceder 512 tokens
) -> List[Dict[str, Any]]:
    """
    Divide un documento en chunks con metadata.
    
    Returns:
        Lista de chunks con formato para vector_io.insert
    """
    chunker = TextChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    text_chunks = chunker.split_text(content)
    
    chunks = []
    chunk_index = 0
    
    for chunk_text in text_chunks:
        # Si el chunk excede el hard limit, dividirlo
        if len(chunk_text) > max_chunk_chars:
            # Dividir en sub-chunks
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
    
    # Actualizar total_chunks
    for chunk in chunks:
        chunk["metadata"]["total_chunks"] = len(chunks)
    
    return chunks


# =============================================================================
# FUNCIONES DE CARGA
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


def create_vector_store(
    openai_client: OpenAI,
    name: str,
    embedding_model: str = EMBEDDING_MODEL,
    embedding_dimension: int = EMBEDDING_DIMENSION
) -> str:
    """Crea un nuevo vector store en Milvus."""
    print(f"\n🗄️  Creando vector store '{name}'...")
    
    vector_store = openai_client.vector_stores.create(
        name=name,
        extra_body={
            "embedding_model": embedding_model,
            "embedding_dimension": embedding_dimension,
            "provider_id": "milvus-remote"
        }
    )
    
    print(f"   ✅ Vector Store ID: {vector_store.id}")
    return vector_store.id


def load_documents_from_directory(directory: Path, extensions: list = None) -> List[Dict]:
    """Carga documentos desde un directorio."""
    if extensions is None:
        extensions = [".md", ".txt", ".rst"]
    
    documents = []
    
    for ext in extensions:
        for file_path in sorted(directory.glob(f"*{ext}")):
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
                print(f"   ⚠️  Error leyendo {file_path}: {e}")
    
    return documents


def load_documents_from_json(json_path: Path) -> List[Dict]:
    """Carga documentos desde un archivo JSON."""
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
    
    raise ValueError(f"Formato de JSON no soportado: {type(data)}")


# =============================================================================
# INSERCIÓN CON CHUNKING LOCAL
# =============================================================================

def insert_chunks_with_vector_io(
    llama_client: LlamaStackClient,
    vector_store_id: str,
    chunks: List[Dict[str, Any]],
    batch_size: int = 1,  # Default a 1 para evitar que un chunk malo falle todo
    verbose: bool = False
) -> int:
    """
    Inserta chunks pre-procesados usando vector_io.insert.
    
    Args:
        llama_client: Cliente de Llama Stack
        vector_store_id: ID del vector store
        chunks: Lista de chunks con formato {chunk_id, content, metadata}
        batch_size: Tamaño del batch para inserción (1 = uno por uno)
        verbose: Mostrar progreso detallado
        
    Returns:
        Número de chunks insertados
    """
    total_inserted = 0
    total_failed = 0
    
    # Insertar en batches (o uno por uno si batch_size=1)
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        
        # Formatear chunks para vector_io.insert
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
                print(f"   ✅ Batch {i//batch_size + 1}: {len(batch)} chunks insertados")
            elif (i + 1) % 100 == 0 or i == len(chunks) - 1:
                print(f"   📊 Progreso: {total_inserted}/{len(chunks)} insertados, {total_failed} errores")
            
        except Exception as e:
            total_failed += len(batch)
            if verbose:
                print(f"   ❌ Error en chunk {i}: {str(e)[:100]}...")
    
    print(f"   ✅ Total insertados: {total_inserted}")
    if total_failed > 0:
        print(f"   ⚠️  Total fallidos: {total_failed}")
    
    return total_inserted


def verify_insertion(
    llama_client: LlamaStackClient,
    vector_store_id: str,
    query: str = "test"
) -> int:
    """Verifica que los chunks se insertaron correctamente."""
    print(f"\n🔍 Verificando inserción con query: '{query}'")
    
    try:
        results = llama_client.vector_io.query(
            vector_db_id=vector_store_id,
            query=query,
            params={"max_chunks": 5}
        )
        
        chunk_count = len(results.chunks) if hasattr(results, 'chunks') else 0
        print(f"   ✅ Query devolvió {chunk_count} chunks")
        
        if chunk_count > 0 and hasattr(results, 'chunks'):
            print(f"\n   📋 Ejemplo de chunk recuperado:")
            chunk = results.chunks[0]
            content = chunk.content[:200] if hasattr(chunk, 'content') else str(chunk)[:200]
            print(f"      {content}...")
        
        return chunk_count
        
    except Exception as e:
        print(f"   ❌ Error verificando: {e}")
        return 0


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Sube documentos a Milvus con chunking LOCAL"
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
        help="Archivo JSON con documentos (alternativa a --documents-dir)"
    )
    
    parser.add_argument(
        "--store-name",
        type=str,
        default=f"lrba_local_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        help="Nombre del vector store a crear"
    )
    
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=DEFAULT_CHUNK_SIZE,
        help=f"Tamaño de chunk en CARACTERES (default: {DEFAULT_CHUNK_SIZE})"
    )
    
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=DEFAULT_CHUNK_OVERLAP,
        help=f"Overlap entre chunks en caracteres (default: {DEFAULT_CHUNK_OVERLAP})"
    )
    
    parser.add_argument(
        "--llama-stack-url",
        type=str,
        default=LLAMA_STACK_URL,
        help="URL del servidor Llama Stack"
    )
    
    parser.add_argument(
        "--embedding-model",
        type=str,
        default=EMBEDDING_MODEL,
        help=f"Modelo de embedding (default: {EMBEDDING_MODEL})"
    )
    
    parser.add_argument(
        "--embedding-dimension",
        type=int,
        default=EMBEDDING_DIMENSION,
        help=f"Dimensión del embedding (default: {EMBEDDING_DIMENSION})"
    )
    
    parser.add_argument(
        "--verify-query",
        type=str,
        default="LRBA",
        help="Query para verificar inserción (default: LRBA)"
    )
    
    parser.add_argument(
        "--batch-size",
        type=int,
        default=1,
        help="Tamaño del batch para inserción (default: 1, uno por uno)"
    )
    
    parser.add_argument(
        "--max-chunk-chars",
        type=int,
        default=450,
        help="Límite máximo de caracteres por chunk (default: 450, para no exceder 512 tokens)"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Mostrar progreso detallado de inserción"
    )
    
    args = parser.parse_args()
    
    # Banner
    print("=" * 70)
    print("📚 UPLOAD DOCUMENTOS A MILVUS CON CHUNKING LOCAL")
    print("=" * 70)
    print(f"   URL: {args.llama_stack_url}")
    print(f"   Embedding Model: {args.embedding_model}")
    print(f"   Embedding Dimension: {args.embedding_dimension}")
    print(f"   Chunk Size: {args.chunk_size} caracteres")
    print(f"   Chunk Overlap: {args.chunk_overlap} caracteres")
    print(f"   Max Chunk Chars: {args.max_chunk_chars} (hard limit)")
    print(f"   Batch Size: {args.batch_size}")
    
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
    
    # Hacer chunking LOCAL
    print(f"\n✂️  Realizando chunking local...")
    all_chunks = []
    for doc in documents:
        doc_chunks = chunk_document(
            content=doc["content"],
            document_id=doc["document_id"],
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap,
            metadata=doc.get("metadata", {}),
            max_chunk_chars=args.max_chunk_chars
        )
        print(f"   📄 {doc['document_id']}: {len(doc_chunks)} chunks")
        all_chunks.extend(doc_chunks)
    
    print(f"\n   📊 Total chunks generados: {len(all_chunks)}")
    
    # Mostrar estadísticas de chunks
    chunk_sizes = [len(c["content"]) for c in all_chunks]
    print(f"   📏 Tamaño promedio: {sum(chunk_sizes)//len(chunk_sizes)} caracteres")
    print(f"   📏 Tamaño mínimo: {min(chunk_sizes)} caracteres")
    print(f"   📏 Tamaño máximo: {max(chunk_sizes)} caracteres")
    
    # Crear vector store
    vector_store_id = create_vector_store(
        openai_client,
        args.store_name,
        args.embedding_model,
        args.embedding_dimension
    )
    
    # Insertar chunks usando vector_io
    print(f"\n📤 Insertando {len(all_chunks)} chunks...")
    inserted = insert_chunks_with_vector_io(
        llama_client,
        vector_store_id,
        all_chunks,
        batch_size=args.batch_size,
        verbose=args.verbose
    )
    
    # Verificar
    verify_insertion(llama_client, vector_store_id, args.verify_query)
    
    # Resumen final
    print("\n" + "=" * 70)
    print("✅ COMPLETADO")
    print("=" * 70)
    print(f"   Vector Store ID: {vector_store_id}")
    print(f"   Store Name: {args.store_name}")
    print(f"   Documentos: {len(documents)}")
    print(f"   Chunks insertados: {inserted}")
    print(f"   Chunk Size: {args.chunk_size} chars")
    print(f"   Chunk Overlap: {args.chunk_overlap} chars")
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
    
    # Guardar información del vector store
    output_info = {
        "vector_store_id": vector_store_id,
        "store_name": args.store_name,
        "documents_count": len(documents),
        "chunks_count": inserted,
        "chunk_size": args.chunk_size,
        "chunk_overlap": args.chunk_overlap,
        "embedding_model": args.embedding_model,
        "embedding_dimension": args.embedding_dimension,
        "timestamp": datetime.now().isoformat()
    }
    
    output_file = Path("output") / f"{args.store_name}_info.json"
    output_file.parent.mkdir(exist_ok=True)
    with open(output_file, "w") as f:
        json.dump(output_info, f, indent=2)
    print(f"   📝 Info guardada en: {output_file}")


if __name__ == "__main__":
    main()

