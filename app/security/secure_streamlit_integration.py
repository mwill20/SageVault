# secure_streamlit_integration.py
"""Minimal security integration for Streamlit app without breaking existing functionality."""

import streamlit as st
import re
from typing import Dict, List, Any, Optional
from .security_utils import (
    redact_secrets, 
    injection_score, 
    penalize_suspicious,
    warn_dangerous,
    sanitize_text
)
from .secure_prompts import SECURE_SYSTEM_PROMPT

class SecurityMiddleware:
    """Lightweight security middleware that wraps existing RAG calls."""
    
    @staticmethod
    def secure_query(query: str) -> tuple[str, bool, List[str]]:
        """
        Process query for security. Returns (safe_query, should_block, warnings)
        """
        if not query or not query.strip():
            return "", False, []
        
        warnings = []
        
        # Check for injection patterns
        inj_score = injection_score(query)
        if inj_score >= 2:  # High threshold to avoid false positives
            return "", True, ["Query contains potential security risks"]
        elif inj_score >= 1:
            warnings.append("Query may contain suspicious patterns")
        
        # Redact any secrets that somehow got into the query
        safe_query = redact_secrets(query)
        
        return safe_query, False, warnings
    
    @staticmethod
    def secure_response(response: str, sources: List[Dict]) -> Dict[str, Any]:
        """
        Process response for security. Returns enhanced response with metadata.
        """
        if not response:
            return {
                "content": "No relevant information found in the provided documents.",
                "sources": [],
                "security_applied": True,
                "redactions": 0
            }
        
        # Count redactions before and after
        original_secret_count = len(re.findall(r'(sk-[A-Za-z0-9]{4,}|ghp_[A-Za-z0-9]{36}|AKIA[0-9A-Z]{16})', response))
        safe_response = redact_secrets(response)
        redaction_count = safe_response.count('[REDACTED]')
        
        # Process sources
        safe_sources = []
        for source in sources:
            safe_source = dict(source)
            if 'text' in safe_source:
                safe_source['text'] = redact_secrets(safe_source['text'])
            safe_sources.append(safe_source)
        
        return {
            "content": safe_response,
            "sources": safe_sources,
            "security_applied": True,
            "redactions": redaction_count
        }
    
    @staticmethod
    def get_secure_system_prompt() -> str:
        """Get the secure system prompt."""
        return SECURE_SYSTEM_PROMPT

def secure_rag_search(original_search_func, query: str, *args, **kwargs) -> Dict[str, Any]:
    """
    Wrapper function for existing RAG search that adds security.
    
    Usage:
    Instead of: results = search_vector_store(collection, query, k=5)
    Use:        results = secure_rag_search(search_vector_store, query, collection, k=5)
    """
    # Apply security to query
    safe_query, should_block, warnings = SecurityMiddleware.secure_query(query)
    
    if should_block:
        return {
            "error": "Query blocked for security reasons",
            "warnings": warnings,
            "results": []
        }
    
    # Show warnings in Streamlit if available
    for warning in warnings:
        try:
            st.warning(f"🔒 Security Notice: {warning}")
        except:
            pass  # Not in Streamlit context
    
    try:
        # Call original search function
        results = original_search_func(safe_query, *args, **kwargs)
        
        # Apply security to results
        if isinstance(results, list):
            secured_results = penalize_suspicious(results, text_key="text")
            return {
                "results": secured_results,
                "query_secured": safe_query != query,
                "warnings": warnings
            }
        else:
            return {
                "results": results,
                "query_secured": safe_query != query, 
                "warnings": warnings
            }
            
    except Exception as e:
        return {
            "error": f"Search failed: {str(e)}",
            "warnings": warnings,
            "results": []
        }

# Convenience functions for easy integration
def add_security_to_streamlit():
    """Add security indicators to Streamlit sidebar."""
    with st.sidebar:
        st.markdown("### 🔒 Security Status")
        st.success("✅ Secret redaction: Active")
        st.success("✅ Injection detection: Active") 
        st.success("✅ Source verification: Active")
        st.info("Security measures are protecting your queries and responses.")

def display_security_info(response_data: Dict[str, Any]):
    """Display security information if available."""
    if not isinstance(response_data, dict):
        return
    
    if response_data.get("security_applied"):
        redactions = response_data.get("redactions", 0)
        if redactions > 0:
            st.info(f"🔒 Security: {redactions} potential secret(s) were redacted from the response.")
    
    warnings = response_data.get("warnings", [])
    for warning in warnings:
        st.warning(f"🔒 Security: {warning}")

# Example integration for your existing Streamlit app
def integrate_security_example():
    """
    Example of how to integrate security into existing Streamlit app with minimal changes.
    
    BEFORE (in your streamlit_app_clean.py):
    ```python
    if user_query:
        results = search_vector_store(collection, user_query, k=5)
        response = generate_response(results)
        st.write(response)
    ```
    
    AFTER (with security):
    ```python
    if user_query:
        # Add security wrapper
        search_result = secure_rag_search(
            lambda q, *args, **kwargs: search_vector_store(*args, q, **kwargs),
            user_query, collection, k=5
        )
        
        if "error" in search_result:
            st.error(search_result["error"])
        else:
            results = search_result["results"]
            response = generate_response(results)
            
            # Secure the response
            secure_resp = SecurityMiddleware.secure_response(response, results)
            st.write(secure_resp["content"])
            display_security_info(secure_resp)
    ```
    """
    pass

__all__ = [
    "SecurityMiddleware",
    "secure_rag_search", 
    "add_security_to_streamlit",
    "display_security_info",
    "integrate_security_example"
]
