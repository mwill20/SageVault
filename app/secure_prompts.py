"""Compatibility shim for legacy secure prompt imports."""
from app.security.secure_prompts import SECURE_SYSTEM_PROMPT, SYSTEM_PROMPT

__all__ = ["SECURE_SYSTEM_PROMPT", "SYSTEM_PROMPT"]
