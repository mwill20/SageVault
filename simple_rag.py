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
        # Documentation formats
        '.md', '.txt', '.rst', '.adoc', '.wiki', '.pdf', '.docx',
        # Programming languages
        '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.h', '.hpp', 
        '.cs', '.php', '.rb', '.go', '.rs', '.swift', '.kt', '.scala',
        # Web technologies
        '.css', '.html', '.htm', '.scss', '.sass', '.less',
        # Configuration and data
        '.json', '.yml', '.yaml', '.xml', '.toml', '.cfg', '.ini', '.conf', '.config',
        # Scripts and data science
        '.sh', '.bash', '.zsh', '.sql', '.r', '.m', '.pl', '.lua', '.vim',
        '.ipynb',  # Jupyter notebooks
        '.dockerfile', '.gitignore', '.env',
        # ML/AI and Data Science formats
        '.csv', '.tsv', '.parquet', '.npy', '.npz', '.pkl', '.pickle',
        # Security and documentation
        '.pem', '.crt', '.key', '.log', '.tex', '.bib'
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

def identify_risky_files(files: Dict[str, str]) -> List[Dict[str, str]]:
    """Identify potentially risky files and return risk assessment"""
    risky_files = []
    
    # High-risk file patterns
    dangerous_extensions = {'.exe', '.bat', '.cmd', '.ps1', '.scr', '.vbs', '.jar'}
    suspicious_extensions = {'.bin', '.dll', '.so', '.dylib'}
    script_extensions = {'.sh', '.bash', '.zsh', '.fish'}
    
    for file_path in files.keys():
        filename_lower = file_path.lower()
        risk_level = None
        reason = None
        
        # Check for dangerous executables
        if any(filename_lower.endswith(ext) for ext in dangerous_extensions):
            risk_level = "HIGH"
            reason = "Executable file that could contain malware or malicious code"
        
        # Check for suspicious binaries
        elif any(filename_lower.endswith(ext) for ext in suspicious_extensions):
            risk_level = "MEDIUM"
            reason = "Binary file that cannot be safely analyzed as text"
        
        # Check for shell scripts (potentially risky but often legitimate)
        elif any(filename_lower.endswith(ext) for ext in script_extensions):
            content = files[file_path][:500].lower()  # Check first 500 chars
            if any(pattern in content for pattern in ['curl', 'wget', 'rm -rf', 'chmod 777', '| sh', '| bash']):
                risk_level = "MEDIUM"
                reason = "Shell script contains potentially dangerous commands"
        
        # Check content for suspicious patterns
        elif not is_safe_file_type(file_path):
            risk_level = "LOW"
            reason = "File type not in standard safe list"
        
        if risk_level:
            risky_files.append({
                'file_path': file_path,
                'risk_level': risk_level,
                'reason': reason,
                'can_override': True
            })
    
    return risky_files

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
            all_metadata.append({
                "file_path": file_path, 
                "chunk_index": i,
                "source_type": "legacy",
                "content_length": len(chunk)
            })
            all_ids.append(f"legacy_{file_path}_{i}")
    
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

def add_to_vector_store(collection: object, documents: Dict[str, str], source_type: str, 
                       source_info: Dict = None, chunk_size: int = 500, overlap_percent: float = 10.0) -> object:
    """Add new documents to existing vector store collection"""
    model = get_embeddings_model()
    
    all_texts = []
    all_metadata = []
    all_ids = []
    doc_count = 0
    
    # Process all documents
    for file_path, content in documents.items():
        if not content or not content.strip():
            continue
            
        chunks = chunk_text(content, chunk_size, overlap_percent)
        for i, chunk in enumerate(chunks):
            if not chunk.strip():
                continue
                
            # Create metadata with source information
            metadata = {
                'file_path': file_path,
                'chunk_index': i,
                'source_type': source_type,  # 'repository' or 'uploaded'
                'content_length': len(chunk)
            }
            
            # Add source-specific information
            if source_info:
                if source_type == 'repository' and 'owner' in source_info and 'repo' in source_info:
                    metadata['repo_owner'] = source_info['owner']
                    metadata['repo_name'] = source_info['repo']
                    metadata['github_url'] = f"https://github.com/{source_info['owner']}/{source_info['repo']}/blob/main/{file_path}"
                elif source_type == 'uploaded':
                    metadata['upload_time'] = source_info.get('upload_time', '')
                    # Add document summary to metadata for better retrieval
                    document_summaries = source_info.get('document_summaries', {})
                    if file_path in document_summaries:
                        metadata['document_summary'] = document_summaries[file_path]
            
            # Use enhanced chunk if we added document summary
            enhanced_chunk = chunk
            if source_type == 'uploaded' and source_info and 'document_summaries' in source_info:
                document_summaries = source_info['document_summaries']
                if file_path in document_summaries:
                    enhanced_chunk = f"Document type: {document_summaries[file_path]}\n\n{chunk}"
            
            all_texts.append(enhanced_chunk)
            all_metadata.append(metadata)
            all_ids.append(f"{source_type}_{file_path}_{i}")
            doc_count += 1
    
    if all_texts:
        # Generate embeddings
        embeddings = model.encode(all_texts)
        
        # Debug: Print what's being added
        print(f"Adding {len(all_texts)} chunks from {source_type} sources to vector store")
        print(f"Sample metadata: {all_metadata[0] if all_metadata else 'None'}")
        
        # Add to existing collection
        collection.add(
            ids=all_ids,
            documents=all_texts,
            metadatas=all_metadata,
            embeddings=embeddings.tolist()
        )
        
        # Debug: Check total count after adding
        total_count = collection.count()
        print(f"Collection now has {total_count} total items after adding {len(all_texts)} {source_type} chunks")
    
    return collection

def create_or_update_unified_vector_store(collection_name: str = "unified_docs") -> object:
    """Create or get existing unified vector store that can contain multiple source types"""
    client = get_chroma_client()
    
    try:
        # Try to get existing collection
        collection = client.get_collection(name=collection_name)
        # Check what's already in the collection
        existing_count = collection.count()
        print(f"Found existing collection '{collection_name}' with {existing_count} items")
    except:
        # Create new collection if it doesn't exist
        collection = client.create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        print(f"Created new collection '{collection_name}'")
    
    return collection

def enhance_query_with_context(query: str, repo_info: Dict = None, top_level_dirs: List[str] = None) -> str:
    """Expand user query with repository context for better retrieval recall"""
    enhanced_parts = [query]
    
    # Add repository context if available
    if repo_info and 'owner' in repo_info and 'repo' in repo_info:
        repo_context = f"{repo_info['owner']}/{repo_info['repo']}"
        enhanced_parts.append(repo_context)
    
    # Add top-level directory context for better structure understanding
    if top_level_dirs:
        # Only add the most relevant directories to avoid query bloat
        excluded_dirs = {'node_modules', '.git', '__pycache__', 'venv', '.env'}
        relevant_dirs = [d for d in top_level_dirs[:5] if d.lower() not in excluded_dirs]
        if relevant_dirs:
            dir_context = " ".join(relevant_dirs)
            enhanced_parts.append(dir_context)
    
    # Join with spaces, maintaining natural language flow
    enhanced_query = " ".join(enhanced_parts)
    return enhanced_query

def search_vector_store(collection: object, query: str, k: int = 5, repo_info: Dict = None, top_level_dirs: List[str] = None) -> List[Dict]:
    """Search the vector store with enhanced query rewriting and README prioritization"""
    model = get_embeddings_model()
    
    # For unified search (repo + uploads), use original query to avoid bias
    # Only enhance query if we're searching repository-only content
    print(f"Original query: {query}")  # Debug
    
    # Create query embedding using original query for unbiased search
    query_embedding = model.encode([query], normalize_embeddings=True)
    
    # Search for more results to ensure we can find README content
    search_k = min(k * 3, 50)  # Search more broadly first
    results = collection.query(
        query_embeddings=query_embedding.tolist(),
        n_results=search_k,
        include=["documents", "metadatas", "distances"]
    )
    
    # Debug: Check what ChromaDB actually returned
    if results["metadatas"] and results["metadatas"][0]:
        raw_source_types = [meta.get("source_type", "unknown") for meta in results["metadatas"][0]]
        print(f"ChromaDB returned {len(raw_source_types)} results with source types: {set(raw_source_types)}")
    else:
        print("ChromaDB returned no results")
    
    # Format results with balanced source handling
    all_results = []
    
    for doc, metadata, distance in zip(
        results["documents"][0], 
        results["metadatas"][0], 
        results["distances"][0]
    ):
        result = {
            "text": doc,
            "file_path": metadata["file_path"],
            "similarity": round(1 - distance, 3),  # Convert distance to similarity
            "source_type": metadata.get("source_type", "unknown"),
            "github_url": metadata.get("github_url", ""),
            "chunk_index": metadata.get("chunk_index", 0)
        }
        all_results.append(result)
    
    # Debug: Show distribution before processing
    before_source_types = [r["source_type"] for r in all_results]
    print(f"Before processing: {len(all_results)} results from {set(before_source_types)}")
    
    # Sort by similarity first
    all_results.sort(key=lambda x: x["similarity"], reverse=True)
    
    # Apply MMR for diversity while ensuring source balance
    if len(all_results) > k:
        # Ensure source diversity by separating source types
        repo_results = [r for r in all_results if r["source_type"] == "repository"]
        uploaded_results = [r for r in all_results if r["source_type"] == "uploaded"]
        
        print(f"Separated: {len(repo_results)} repo, {len(uploaded_results)} uploaded")
        
        # If we have both types, ensure both are represented
        if repo_results and uploaded_results:
            # Take best from each source type, then fill with MMR
            final_results = []
            final_results.append(repo_results[0])  # Best repo result
            final_results.append(uploaded_results[0])  # Best uploaded result
            
            # Fill remaining with MMR from all results
            remaining_k = k - 2
            if remaining_k > 0:
                mmr_results = apply_mmr(all_results[2:], query_embedding[0], remaining_k, lambda_param=0.5)
                final_results.extend(mmr_results)
        else:
            # Only one source type, use normal MMR
            final_results = apply_mmr(all_results, query_embedding[0], k, lambda_param=0.5)
    else:
        final_results = all_results[:k]
    
    # Debug: Print what's being returned
    source_types = [r.get('source_type', 'unknown') for r in final_results[:k]]
    print(f"Search returning {len(final_results[:k])} results from sources: {set(source_types)}")
    
    return final_results[:k]

def apply_mmr(candidates: List[Dict], query_embedding: List[float], k: int, lambda_param: float = 0.7) -> List[Dict]:
    """Apply Maximal Marginal Relevance to balance similarity and novelty"""
    if not candidates or k <= 0:
        return []
    
    # Debug: Show input distribution
    input_sources = [c["source_type"] for c in candidates]
    print(f"MMR input: {len(candidates)} candidates from {set(input_sources)}")
    
    model = get_embeddings_model()
    selected = []
    remaining = candidates.copy()
    
    # First selection: highest similarity to query
    best_candidate = max(remaining, key=lambda x: x["similarity"])
    selected.append(best_candidate)
    remaining.remove(best_candidate)
    
    # Get embeddings for remaining candidates
    remaining_texts = [c["text"] for c in remaining]
    if not remaining_texts:
        return selected
    
    remaining_embeddings = model.encode(remaining_texts, normalize_embeddings=True)
    
    # Iteratively select based on MMR score
    while len(selected) < k and remaining:
        mmr_scores = []
        
        for i, candidate in enumerate(remaining):
            # Similarity to query (relevance)
            sim_to_query = candidate["similarity"]
            
            # Maximum similarity to already selected items (redundancy)
            max_sim_to_selected = 0.0
            if selected:
                candidate_emb = remaining_embeddings[i:i+1]
                selected_texts = [s["text"] for s in selected]
                selected_embs = model.encode(selected_texts, normalize_embeddings=True)
                
                # Calculate cosine similarities
                similarities = []
                for selected_emb in selected_embs:
                    # Cosine similarity = dot product of normalized vectors
                    try:
                        import numpy as np
                        sim = float(np.dot(candidate_emb[0], selected_emb))
                    except:
                        # Fallback to manual calculation
                        sim = sum(a * b for a, b in zip(candidate_emb[0], selected_emb))
                    similarities.append(sim)
                max_sim_to_selected = max(similarities) if similarities else 0.0
            
            # MMR score: lambda * relevance - (1-lambda) * redundancy
            mmr_score = lambda_param * sim_to_query - (1 - lambda_param) * max_sim_to_selected
            mmr_scores.append((mmr_score, i, candidate))
        
        # Select candidate with highest MMR score
        if mmr_scores:
            _, best_idx, best_candidate = max(mmr_scores, key=lambda x: x[0])
            selected.append(best_candidate)
            remaining.remove(best_candidate)
            # Remove corresponding embedding
            remaining_embeddings = [emb for j, emb in enumerate(remaining_embeddings) if j != best_idx]
        else:
            break
    
    # Debug: Show output distribution
    output_sources = [s["source_type"] for s in selected]
    print(f"MMR output: {len(selected)} results from {set(output_sources)}")
    
    return selected