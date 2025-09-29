# secure_rag.py
"""Security-enhanced RAG implementation that maintains source tagging while adding comprehensive security measures."""

import re
from typing import List, Dict, Any, Optional, Tuple
from app.security_gate import secure_text, secure_plan
from app.security_utils import (
    penalize_suspicious, 
    diversity_guard, 
    redact_secrets,
    injection_score,
    warn
)

class SecureRAGMixin:
    """Mixin to add security features to existing RAG functionality without breaking it."""
    
    def secure_query_preprocessing(self, query: str) -> Tuple[str, Dict[str, Any]]:
        """Preprocess and analyze query for security risks."""
        if not query:
            return "", {"risk_score": 0.0, "warnings": []}
        
        # Security analysis
        injection_risk = injection_score(query)
        risk_score = min(injection_risk / 10.0, 1.0)  # Normalize to 0-1
        
        warnings = []
        if injection_risk >= 1:
            warnings.append("Query contains potential injection patterns")
        
        # Redact any secrets in the query
        cleaned_query = redact_secrets(query)
        
        # Sanitize query text
        safe_query = secure_text(cleaned_query)
        
        security_context = {
            "risk_score": risk_score,
            "warnings": warnings,
            "injection_score": injection_risk,
            "original_length": len(query),
            "cleaned_length": len(safe_query)
        }
        
        return safe_query, security_context
    
    def secure_retrieval_filtering(self, retrieval_results: List[Dict], max_results: int = 10) -> List[Dict]:
        """Apply security filtering to retrieval results."""
        if not retrieval_results:
            return []
        
        # Apply injection pattern penalization
        secured_results = penalize_suspicious(retrieval_results, text_key="text")
        
        # Apply diversity guard to prevent overwhelming from single source
        diverse_results = diversity_guard(secured_results, key="path", max_per_key=3)
        
        # Sort by adjusted similarity (security penalties already applied)
        sorted_results = sorted(diverse_results, key=lambda x: x.get("similarity", 0.0), reverse=True)
        
        # Limit results and add security metadata
        final_results = []
        for i, result in enumerate(sorted_results[:max_results]):
            secured_result = dict(result)
            secured_result["security_rank"] = i + 1
            secured_result["security_filtered"] = True
            
            # Redact any secrets in the content
            if "text" in secured_result:
                secured_result["text"] = redact_secrets(secured_result["text"])
            
            final_results.append(secured_result)
        
        return final_results
    
    def secure_response_formatting(self, response: str, sources: List[Dict], repo_name: str = "Repository") -> Dict[str, Any]:
        """Format response with security measures and source attribution."""
        if not response:
            return {
                "response": "No relevant information found in the provided documents.",
                "sources": [],
                "security_status": "safe",
                "warnings": []
            }
        
        # Security analysis of response
        warnings = []
        security_status = "safe"
        
        # Check for potential secret leakage
        if re.search(r'(sk-[A-Za-z0-9]{4,}|ghp_[A-Za-z0-9]{36}|AKIA[0-9A-Z]{16})', response):
            warnings.append("Response may contain redacted credentials")
            security_status = "warning"
        
        # Redact secrets in response
        safe_response = redact_secrets(response)
        
        # Ensure proper source attribution format
        formatted_response = self._format_with_source_attribution(safe_response, sources, repo_name)
        
        return {
            "response": formatted_response,
            "sources": self._format_secure_sources(sources),
            "security_status": security_status,
            "warnings": warnings,
            "repo_name": repo_name
        }
    
    def _format_with_source_attribution(self, response: str, sources: List[Dict], repo_name: str) -> str:
        """Ensure response includes proper source attribution headers."""
        if not sources:
            return response
        
        # Check if response already has source attribution
        has_repo_attr = f"**Repo: {repo_name}**" in response or "**Repo:" in response
        has_download_attr = "**Download:" in response
        
        # If already properly formatted, return as-is
        if has_repo_attr or has_download_attr:
            return response
        
        # Otherwise, add source attribution
        repo_sources = [s for s in sources if not s.get("path", "").startswith("uploaded:")]
        download_sources = [s for s in sources if s.get("path", "").startswith("uploaded:")]
        
        attribution_parts = []
        if repo_sources:
            attribution_parts.append(f"**Repo: {repo_name}**")
        if download_sources:
            download_files = [s.get("path", "").replace("uploaded:", "") for s in download_sources[:3]]
            attribution_parts.append(f"**Download: {', '.join(download_files)}**")
        
        if attribution_parts:
            attribution = "\n\n" + "\n".join(attribution_parts) + "\n\n"
            return response + attribution
        
        return response
    
    def _format_secure_sources(self, sources: List[Dict]) -> List[Dict]:
        """Format sources with security metadata."""
        secure_sources = []
        for source in sources:
            secure_source = dict(source)
            
            # Redact any secrets in source paths or content
            if "path" in secure_source:
                secure_source["path"] = redact_secrets(secure_source["path"])
            if "text" in secure_source:
                secure_source["text"] = redact_secrets(secure_source["text"])
            
            # Add security metadata
            secure_source["security_verified"] = True
            secure_sources.append(secure_source)
        
        return secure_sources

def create_secure_rag_wrapper(existing_rag_class):
    """Factory function to create a security-enhanced version of existing RAG class."""
    
    class SecureRAG(existing_rag_class, SecureRAGMixin):
        """Security-enhanced RAG that wraps existing functionality."""
        
        def search_with_security(self, query: str, repo_name: str = "Repository", **kwargs) -> Dict[str, Any]:
            """Secure version of search functionality."""
            # Preprocess query for security
            safe_query, security_context = self.secure_query_preprocessing(query)
            
            if security_context["risk_score"] > 0.8:
                return {
                    "response": "Query rejected due to security concerns. Please rephrase your request.",
                    "sources": [],
                    "security_status": "rejected",
                    "warnings": security_context["warnings"]
                }
            
            # Perform original search with secure query
            try:
                # Call parent search method (assuming it exists)
                if hasattr(super(), 'search_vector_store'):
                    results = super().search_vector_store(safe_query, **kwargs) # type: ignore
                else:
                    # Fallback - implement basic search
                    results = []
                
                # Apply security filtering
                secure_results = self.secure_retrieval_filtering(results)
                
                # Generate response (this would need integration with your LLM)
                response = self._generate_secure_response(safe_query, secure_results, repo_name)
                
                # Format final response with security measures
                return self.secure_response_formatting(response, secure_results, repo_name)
                
            except Exception as e:
                warn(f"RAG search failed: {str(e)}")
                return {
                    "response": "Search temporarily unavailable due to technical issues.",
                    "sources": [],
                    "security_status": "error",
                    "warnings": ["Technical error occurred during search"]
                }
        
        def _generate_secure_response(self, query: str, results: List[Dict], repo_name: str) -> str:
            """Generate response with security considerations - placeholder for LLM integration."""
            if not results:
                return "No relevant information found in the provided documents."
            
            # This would integrate with your LLM system
            # For now, return a simple formatted response
            response_parts = []
            
            repo_results = [r for r in results if not r.get("path", "").startswith("uploaded:")]
            download_results = [r for r in results if r.get("path", "").startswith("uploaded:")]
            
            if repo_results:
                response_parts.append(f"**Repo: {repo_name}**")
                response_parts.append("Repository information available in search results.")
            
            if download_results:
                filenames = [r.get("path", "").replace("uploaded:", "") for r in download_results[:3]]
                response_parts.append(f"**Download: {', '.join(filenames)}**")
                response_parts.append("Additional information available in uploaded documents.")
            
            return "\n\n".join(response_parts)
    
    return SecureRAG

# Export for easy integration
__all__ = ["SecureRAGMixin", "create_secure_rag_wrapper"]