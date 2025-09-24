"""Clean RAG utilities - minimal and reliable"""
import os
import re
from typing import Dict, List

# Silence ChromaDB telemetry
os.environ["ANONYMIZED_TELEMETRY"] = "false"
os.environ["CHROMADB_DISABLE_TELEMETRY"] = "true"

# Global singletons
_chroma_client = None
_embeddings_model = None

def get_chroma_client():
    """Get or create ChromaDB client"""
    global _chroma_client
    if _chroma_client is None:
        import chromadb
        from chromadb.config import Settings
        _chroma_client = chromadb.Client(Settings(anonymized_telemetry=False))
    return _chroma_client

def get_embeddings_model():
    """Get or create sentence transformer model"""
    global _embeddings_model
    if _embeddings_model is None:
        from sentence_transformers import SentenceTransformer
        _embeddings_model = SentenceTransformer("all-MiniLM-L6-v2")
    return _embeddings_model

def chunk_text(text: str, max_chars: int = 500, overlap: int = 50) -> List[str]:
    """Simple text chunking with overlap"""
    if not text or len(text) <= max_chars:
        return [text] if text else []
    
    chunks = []
    start = 0
    while start < len(text):
        end = start + max_chars
        if end >= len(text):
            chunks.append(text[start:])
            break
        
        # Try to break at sentence or paragraph boundary
        chunk = text[start:end]
        last_period = chunk.rfind('.')
        last_newline = chunk.rfind('\n')
        
        if last_period > max_chars * 0.7:
            end = start + last_period + 1
        elif last_newline > max_chars * 0.7:
            end = start + last_newline + 1
            
        chunks.append(text[start:end])
        start = end - overlap
    
    return [c.strip() for c in chunks if c.strip()]

def create_vector_store(documents: Dict[str, str], collection_name: str = "docs") -> object:
    """Create ChromaDB collection from documents"""
    client = get_chroma_client()
    model = get_embeddings_model()
    
    # Delete existing collection if it exists
    try:
        client.delete_collection(collection_name)
    except:
        pass
    
    collection = client.create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}
    )
    
    # Process all documents
    all_chunks = []
    all_metadata = []
    all_ids = []
    
    for file_path, content in documents.items():
        chunks = chunk_text(content)
        for i, chunk in enumerate(chunks):
            all_chunks.append(chunk)
            all_metadata.append({"file_path": file_path, "chunk_id": i})
            all_ids.append(f"{file_path}::{i}")
    
    if all_chunks:
        # Create embeddings
        embeddings = model.encode(all_chunks, normalize_embeddings=True)
        
        # Add to collection
        collection.add(
            ids=all_ids,
            documents=all_chunks,
            metadatas=all_metadata,
            embeddings=embeddings.tolist()
        )
    
    return collection

def search_vector_store(collection: object, query: str, k: int = 5) -> List[Dict]:
    """Search the vector store"""
    model = get_embeddings_model()
    
    # Create query embedding
    query_embedding = model.encode([query], normalize_embeddings=True)
    
    # Search
    results = collection.query(
        query_embeddings=query_embedding.tolist(),
        n_results=k,
        include=["documents", "metadatas", "distances"]
    )
    
    # Format results
    formatted_results = []
    for doc, metadata, distance in zip(
        results["documents"][0], 
        results["metadatas"][0], 
        results["distances"][0]
    ):
        formatted_results.append({
            "text": doc,
            "file_path": metadata["file_path"],
            "chunk_id": metadata["chunk_id"],
            "similarity": round(1 - distance, 3)  # Convert distance to similarity
        })
    
    return formatted_results