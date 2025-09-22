# app/rag_utils.py
from __future__ import annotations
import re
from typing import Dict, List
import chromadb
from chromadb.config import Settings

# Singleton client cache to avoid 'instance already exists with different settings' errors
_CHROMA_CLIENT = None
def _client():
    global _CHROMA_CLIENT
    if _CHROMA_CLIENT is None:
        _CHROMA_CLIENT = chromadb.Client(Settings(anonymized_telemetry=False))
    return _CHROMA_CLIENT
from sentence_transformers import SentenceTransformer

# --- Chunking parameters (adjusted as requested) ---
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

# Lazy-load the small, fast model
_MODEL = None
def _model():
    global _MODEL
    if _MODEL is None:
        _MODEL = SentenceTransformer("all-MiniLM-L6-v2")  # downloads on first use
    return _MODEL

def chunk_markdown(text: str, max_chars: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    # Split on blank lines or headings, then window into fixed-size chunks
    parts = re.split(r"\n(?=#)|\n{2,}", text or "")
    chunks: List[str] = []
    for p in (s.strip() for s in parts):
        if not p: 
            continue
        while len(p) > max_chars:
            chunks.append(p[:max_chars])
            p = p[max_chars - overlap:]
        chunks.append(p)
    return chunks

def build_store(corpus: Dict[str, str], name: str = "repo", *, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP):
    """Build an in-memory Chroma collection from a text corpus.

    Telemetry is explicitly disabled to avoid noisy 'Failed to send telemetry' errors
    observed in some environments where the internal capture signature changes.
    """
    client = _client()  # reuse singleton to prevent settings mismatch on rerun
    col = client.get_or_create_collection(name, metadata={"hnsw:space": "cosine"})

    # Clear previous run (Streamlit reruns often)
    try:
        col.delete(where={})
    except Exception:
        pass

    ids, docs, metas = [], [], []
    for path, text in corpus.items():
        for i, ch in enumerate(chunk_markdown(text, max_chars=chunk_size, overlap=overlap)):
            ids.append(f"{path}::{i}")
            docs.append(ch)
            metas.append({"path": path, "chunk": i})

    # ✅ Guard: nothing to embed
    if not docs:
        return col

    embs = _model().encode(docs, normalize_embeddings=True).tolist()
    col.upsert(ids=ids, documents=docs, metadatas=metas, embeddings=embs)
    return col


def retrieve(col, query: str, k: int = 4):
    q = _model().encode([query], normalize_embeddings=True).tolist()
    res = col.query(query_embeddings=q, n_results=k, include=["documents", "metadatas", "distances"])
    hits = []
    for doc, meta, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0]):
        # Convert distance to a friendlier similarity score (approx)
        hits.append({"path": meta["path"], "chunk": meta["chunk"], "text": doc, "similarity": round(1 - dist, 3)})
    return hits
