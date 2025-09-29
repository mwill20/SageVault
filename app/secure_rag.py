"""Compatibility shim for legacy secure RAG imports."""
from app.security.secure_rag import SecureRAGMixin, create_secure_rag_wrapper

__all__ = ["SecureRAGMixin", "create_secure_rag_wrapper"]
