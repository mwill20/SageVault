"""Compatibility shim for legacy security_gate imports."""
from app.security.security_gate import secure_text, secure_plan

__all__ = ["secure_text", "secure_plan"]
