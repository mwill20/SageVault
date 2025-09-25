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

def is_safe_file_type(filename: str) -> bool:
    """Check if file type is safe for processing"""
    filename_lower = filename.lower()
    
    # Safe text/code file extensions
    safe_extensions = {
        '.md', '.txt', '.rst', '.adoc', '.wiki',
        '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.h', '.hpp', 
        '.cs', '.php', '.rb', '.go', '.rs', '.swift', '.kt', '.scala',
        '.css', '.html', '.htm', '.scss', '.sass', '.less',
        '.json', '.yml', '.yaml', '.xml', '.toml', '.cfg', '.ini', '.conf', '.config',
        '.sh', '.bash', '.zsh', '.sql', '.r', '.m', '.pl', '.lua', '.vim',
        '.ipynb',  # Jupyter notebooks
        '.dockerfile', '.gitignore', '.env'
    }
    
    # Safe files without extensions
    safe_names = {'readme', 'license', 'changelog', 'contributing', 'authors', 
                  'credits', 'makefile', 'dockerfile', 'requirements'}
    
    # Check extension
    for ext in safe_extensions:
        if filename_lower.endswith(ext):
            return True
    
    # Check filename without extension
    base_name = filename_lower.split('.')[0]
    if base_name in safe_names:
        return True
    
    return False

def chunk_text(text: str, max_chars: int = 500, overlap_percent: float = 10.0) -> List[str]:
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
        # Calculate overlap in characters
        overlap = int(max_chars * overlap_percent / 100)
        start = max(end - overlap, start + 1)  # Ensure progress
    
    return [c.strip() for c in chunks if c.strip()]

def create_vector_store(documents: Dict[str, str], collection_name: str = "docs", 
                       chunk_size: int = 500, overlap_percent: float = 10.0) -> object:
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
        chunks = chunk_text(content, chunk_size, overlap_percent)
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
    """Search the vector store with README prioritization"""
    model = get_embeddings_model()
    
    # Create query embedding
    query_embedding = model.encode([query], normalize_embeddings=True)
    
    # Search for more results to ensure we can find README content
    search_k = min(k * 3, 50)  # Search more broadly first
    results = collection.query(
        query_embeddings=query_embedding.tolist(),
        n_results=search_k,
        include=["documents", "metadatas", "distances"]
    )
    
    # Format results with README prioritization
    readme_results = []
    other_results = []
    
    for doc, metadata, distance in zip(
        results["documents"][0], 
        results["metadatas"][0], 
        results["distances"][0]
    ):
        result = {
            "text": doc,
            "file_path": metadata["file_path"],
            "chunk_id": metadata["chunk_id"],
            "similarity": round(1 - distance, 3)  # Convert distance to similarity
        }
        
        # Prioritize README files
        file_name = metadata["file_path"].lower()
        if any(readme_name in file_name for readme_name in ['readme', 'read_me']):
            readme_results.append(result)
        else:
            other_results.append(result)
    
    # Combine results: README first, then others by similarity
    readme_results.sort(key=lambda x: x["similarity"], reverse=True)
    other_results.sort(key=lambda x: x["similarity"], reverse=True)
    
    # Ensure at least one README is included if available
    final_results = []
    if readme_results:
        final_results.append(readme_results[0])  # Always include top README
        remaining_k = k - 1
        
        # Add remaining results (mix of README and others)
        all_remaining = readme_results[1:] + other_results
        all_remaining.sort(key=lambda x: x["similarity"], reverse=True)
        final_results.extend(all_remaining[:remaining_k])
    else:
        final_results = other_results[:k]
    
    return final_results[:k]