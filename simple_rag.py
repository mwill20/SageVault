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

def chunk_text(text: str, max_chars: int = 800, overlap_percent: float = 15.0) -> List[str]:
    """Smart text chunking with overlap and section awareness"""
    if not text or len(text) <= max_chars:
        return [text] if text else []
    
    chunks = []
    start = 0
    while start < len(text):
        end = start + max_chars
        if end >= len(text):
            chunks.append(text[start:])
            break
        
        # Try to break at semantic boundaries (headers, paragraphs, sentences)
        chunk = text[start:end]
        
        # Look for markdown headers first (preserve sections)
        header_match = chunk.rfind('\n## ')
        if header_match == -1:
            header_match = chunk.rfind('\n# ')
        if header_match == -1:
            header_match = chunk.rfind('\n### ')
            
        # Then paragraph breaks
        double_newline = chunk.rfind('\n\n')
        last_period = chunk.rfind('.')
        last_newline = chunk.rfind('\n')
        
        # Prioritize semantic boundaries
        if header_match > max_chars * 0.5:
            end = start + header_match + 1
        elif double_newline > max_chars * 0.6:
            end = start + double_newline + 2
        elif last_period > max_chars * 0.7:
            end = start + last_period + 1
        elif last_newline > max_chars * 0.7:
            end = start + last_newline + 1
            
        chunks.append(text[start:end])
        # Calculate overlap in characters
        overlap = int(max_chars * overlap_percent / 100)
        start = max(end - overlap, start + 1)  # Ensure progress
    
    return [c.strip() for c in chunks if c.strip()]

def create_vector_store(documents: Dict[str, str], collection_name: str = "docs", 
                       chunk_size: int = 800, overlap_percent: float = 15.0) -> object:
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

def calculate_semantic_boost(text: str, file_path: str, query: str) -> float:
    """Calculate semantic boost score for prioritizing important content"""
    boost = 1.0
    
    # Boost for README files
    if 'readme' in file_path.lower():
        boost *= 1.5
        
        # Extra boost for project description sections
        text_lower = text.lower()
        if any(phrase in text_lower for phrase in [
            'what is', 'is a', 'platform that', 'system that', 'tool that',
            'enterprise-grade', 'production-ready', '## 🚀 what is'
        ]):
            boost *= 1.8
            
        # Boost for overview/intro sections
        if any(phrase in text_lower for phrase in [
            '## overview', '## introduction', '## about', '## description',
            'core capabilities', 'main features', 'key features'
        ]):
            boost *= 1.4
    
    # Boost for query-specific content
    query_lower = query.lower()
    if 'what is' in query_lower or 'about' in query_lower:
        if any(phrase in text.lower() for phrase in [
            'transforms how', 'platform', 'system', 'application', 'tool'
        ]):
            boost *= 1.3
    
    return boost

def search_vector_store(collection: object, query: str, k: int = 5, repo_info: Dict = None, top_level_dirs: List[str] = None) -> List[Dict]:
    """Search the vector store with enhanced query rewriting, README prioritization, and semantic boosting"""
    model = get_embeddings_model()
    
    # Enhance query with repository context for better recall
    enhanced_query = enhance_query_with_context(query, repo_info, top_level_dirs)
    
    # Create query embedding using enhanced query
    query_embedding = model.encode([enhanced_query], normalize_embeddings=True)
    
    # Search for more results to ensure we can find README content
    search_k = min(k * 3, 50)  # Search more broadly first
    results = collection.query(
        query_embeddings=query_embedding.tolist(),
        n_results=search_k,
        include=["documents", "metadatas", "distances"]
    )
    
    # Organize results by source type for balanced representation
    repo_results = []
    download_results = []
    other_results = []
    
    for doc, metadata, distance in zip(
        results["documents"][0], 
        results["metadatas"][0], 
        results["distances"][0]
    ):
        base_similarity = round(1 - distance, 3)  # Convert distance to similarity
        
        # Apply semantic boost (reduced for better balance)
        boost_factor = calculate_semantic_boost(doc, metadata["file_path"], query)
        # Cap boost factor to prevent overwhelming other sources
        boost_factor = min(boost_factor, 1.3)  # Reduced from unlimited
        boosted_similarity = min(base_similarity * boost_factor, 1.0)
        
        result = {
            "text": doc,
            "file_path": metadata["file_path"],
            "chunk_id": metadata["chunk_id"],
            "similarity": round(boosted_similarity, 3),
            "original_similarity": base_similarity,
            "boost_factor": round(boost_factor, 2),
            "source_type": metadata.get("actual_source", metadata.get("source_type", "unknown"))
        }
        
        # Categorize by actual source type
        actual_source = metadata.get("actual_source", metadata.get("source_type", "unknown"))
        if actual_source == "Download" or metadata["file_path"].startswith("uploaded:"):
            download_results.append(result)
        elif actual_source == "Repo" or not metadata["file_path"].startswith("uploaded:"):
            repo_results.append(result)
        else:
            other_results.append(result)
    
    # Sort each source type by similarity
    repo_results.sort(key=lambda x: x["similarity"], reverse=True)
    download_results.sort(key=lambda x: x["similarity"], reverse=True)
    other_results.sort(key=lambda x: x["similarity"], reverse=True)
    
    # Ensure balanced representation from available sources
    final_results = []
    
    # For "two sources" or similar queries, ensure we show both if available
    query_lower = query.lower()
    if any(phrase in query_lower for phrase in ['two sources', 'separate sources', 'both sources', 'sources']):
        # Prioritize showing content from each available source
        sources_represented = 0
        if repo_results:
            final_results.extend(repo_results[:2])  # Top 2 from repo
            sources_represented += 1
        if download_results:
            final_results.extend(download_results[:2])  # Top 2 from downloads
            sources_represented += 1
        
        # Fill remaining slots with best overall results
        remaining_slots = k - len(final_results)
        if remaining_slots > 0:
            all_remaining = [r for r in (repo_results[2:] + download_results[2:] + other_results) if r not in final_results]
            all_remaining.sort(key=lambda x: x["similarity"], reverse=True)
            final_results.extend(all_remaining[:remaining_slots])
    
    # For other queries, use the original logic but with better balance
    elif any(phrase in query_lower for phrase in ['what is', 'about', 'tell me about', 'describe']):
        # For descriptive queries, prioritize repo content but ensure downloads are included
        if repo_results:
            final_results.append(repo_results[0])  # Best repo result first
        if download_results:
            final_results.append(download_results[0])  # Best download result
        
        # Fill remaining with mixed results
        remaining_slots = k - len(final_results)
        if remaining_slots > 0:
            all_remaining = [r for r in (repo_results[1:] + download_results[1:] + other_results) if r not in final_results]
            all_remaining.sort(key=lambda x: x["similarity"], reverse=True)
            final_results.extend(all_remaining[:remaining_slots])
    
    # If we have results, return them; otherwise fall back to original logic
    if final_results:
        return final_results[:k]
    
    # Fallback: Apply MMR for diversity with balanced source representation
    all_candidates = repo_results + download_results + other_results
    # Final fallback: use MMR for diversity if no special handling applied
    if len(all_candidates) > k:
        final_results = apply_mmr(all_candidates, query_embedding[0], k, lambda_param=0.7)
    else:
        final_results = all_candidates[:k]
    
    return final_results[:k]

def apply_mmr(candidates: List[Dict], query_embedding: List[float], k: int, lambda_param: float = 0.7) -> List[Dict]:
    """Apply Maximal Marginal Relevance to balance similarity and novelty"""
    if not candidates or k <= 0:
        return []
    
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
    
    return selected

def add_to_vector_store(collection: object, documents: Dict[str, str], source_type: str, 
                       metadata: Dict = None, chunk_size: int = 800, overlap_percent: float = 15.0) -> object:
    """Add documents to existing vector store with source type tracking"""
    model = get_embeddings_model()
    
    # Process all documents
    all_chunks = []
    all_metadata = []
    all_ids = []
    
    for file_path, content in documents.items():
        chunks = chunk_text(content, chunk_size, overlap_percent)
        for i, chunk in enumerate(chunks):
            # Add source tag prefix to chunk content
            if source_type == "unified":
                # Determine actual source type from file_path
                if file_path.startswith("uploaded:"):
                    actual_source = "Download"
                    clean_filename = file_path.replace("uploaded:", "")
                    tagged_chunk = f"[Source: Download - {clean_filename}]\n\n{chunk}"
                else:
                    actual_source = "Repo"
                    # Extract repo name from metadata if available, otherwise use generic
                    repo_name = metadata.get('repo_name', 'Repository')
                    tagged_chunk = f"[Source: Repo - {repo_name}/{file_path}]\n\n{chunk}"
            else:
                actual_source = source_type
                tagged_chunk = f"[Source: {source_type} - {file_path}]\n\n{chunk}"
            
            all_chunks.append(tagged_chunk)
            chunk_metadata = {
                "file_path": file_path, 
                "chunk_id": i,
                "source_type": source_type,
                "actual_source": actual_source,
                "content_length": len(chunk),
                "tagged_length": len(tagged_chunk)
            }
            # Merge additional metadata if provided
            if metadata:
                chunk_metadata.update(metadata)
            all_metadata.append(chunk_metadata)
            all_ids.append(f"{source_type}::{file_path}::{i}")
    
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

def create_or_update_unified_vector_store(collection_name: str = "unified_docs") -> object:
    """Create or update unified vector store that combines all sources"""
    client = get_chroma_client()
    
    # Try to get existing collection, create if it doesn't exist
    try:
        collection = client.get_collection(collection_name)
    except:
        collection = client.create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
    
    return collection