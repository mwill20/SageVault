"""Compatibility shim for legacy imports of security integration helpers."""
from app.security.secure_streamlit_integration import (
    SecurityMiddleware,
    secure_rag_search,
    add_security_to_streamlit,
    display_security_info,
    integrate_security_example,
)

__all__ = [
    "SecurityMiddleware",
    "secure_rag_search",
    "add_security_to_streamlit",
    "display_security_info",
    "integrate_security_example",
]
