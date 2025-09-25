"""RAG utilities with lazy-loaded heavy deps.

Defers importing chromadb and sentence-transformers until needed so that simply
importing this module (e.g., by a smoke test) doesn't require those packages.
"""
from __future__ import annotations
import os
import re
from typing import Dict, List

# Singleton client cache to avoid 'instance already exists with different settings' errors
_CHROMA_CLIENT = None
def _client():
    """Return a singleton chromadb client; imports chromadb on first use."""
    global _CHROMA_CLIENT
    if _CHROMA_CLIENT is None:
        # Best-effort: disable telemetry via env before importing
        os.environ.setdefault("ANONYMIZED_TELEMETRY", "false")
        os.environ.setdefault("CHROMADB_DISABLE_TELEMETRY", "true")
        
        import chromadb  # lazy import
        from chromadb.config import Settings  # lazy import
        
        import chromadb  # lazy import
        from chromadb.config import Settings  # lazy import
            
        _CHROMA_CLIENT = chromadb.Client(Settings(anonymized_telemetry=False))
        # Extra guard: silence telemetry capture if present (API varies across versions)
        try:
            # Common logger silencing (if used internally)
            import logging
            logging.getLogger("chromadb.telemetry").setLevel(logging.CRITICAL)
            logging.getLogger("chromadb").setLevel(logging.ERROR)
        except Exception:
            pass
        try:
            # Comprehensive telemetry capture silencing across multiple potential API surfaces
            import chromadb.telemetry as tel_module
            
            # Replace module-level capture function if it exists
            if hasattr(tel_module, "capture"):
                tel_module.capture = lambda *args, **kwargs: None
                
            # Replace instance-level capture methods on common telemetry objects
            tel = getattr(chromadb, "telemetry", None)
            if tel is not None:
                if hasattr(tel, "capture"):
                    tel.capture = lambda *args, **kwargs: None  # type: ignore[assignment]
                # Some versions expose nested telemetry objects
                for attr in ("telemetry", "_telemetry", "client"):
                    obj = getattr(tel, attr, None)
                    if obj is not None and hasattr(obj, "capture"):
                        try:
                            obj.capture = lambda *args, **kwargs: None  # type: ignore[attr-defined]
                        except Exception:
                            pass
                            
            # Also try to patch any global telemetry client instances
            try:
                import chromadb.telemetry.posthog as posthog_tel
                if hasattr(posthog_tel, "capture"):
                    posthog_tel.capture = lambda *args, **kwargs: None
            except ImportError:
                pass
                
        except Exception:
            # If chroma internals change, we silently ignore; Settings() already disables telemetry
            pass
    return _CHROMA_CLIENT

# --- Chunking parameters (adjusted as requested) ---
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

# Lazy-load the small, fast model
_MODEL = None
def _model():
    """Return a singleton sentence-transformers model; imports on first use."""
    global _MODEL
    if _MODEL is None:
        from sentence_transformers import SentenceTransformer  # lazy import
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
