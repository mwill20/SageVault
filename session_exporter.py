"""
🚀 SageVault Session Export
One-click export of Q&A sessions with cited sources, GitHub links, and similarity scores.
"""

import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import re

@dataclass
class CitedSource:
    """Represents a source citation with metadata"""
    filename: str
    github_url: Optional[str]
    similarity_score: float
    content_snippet: str
    line_numbers: Optional[str] = None

@dataclass
class QASession:
    """Represents a Q&A interaction with sources"""
    question: str
    answer: str
    provider: str
    timestamp: str
    sources: List[CitedSource]
    performance_metrics: Optional[Dict[str, Any]] = None

class SessionExporter:
    """
    Export Q&A sessions to Markdown format with rich source citations
    Perfect for sharing study notes and ensuring reproducibility
    """
    
    def __init__(self):
        self.sessions: List[QASession] = []
        self.repo_url_base: Optional[str] = None
    
    def set_repository_url(self, repo_url: str):
        """Set the GitHub repository base URL for generating source links"""
        # Clean up URL to get base format
        if repo_url.endswith('.git'):
            repo_url = repo_url[:-4]
        if repo_url.startswith('git@github.com:'):
            repo_url = repo_url.replace('git@github.com:', 'https://github.com/')
        
        self.repo_url_base = repo_url
    
    def add_session(self, 
                   question: str, 
                   answer: str, 
                   provider: str,
                   sources: List[Dict[str, Any]],
                   performance_metrics: Optional[Dict[str, Any]] = None):
        """Add a Q&A session to the export queue"""
        
        # Process sources into CitedSource objects
        cited_sources = []
        for source in sources:
            github_url = self._generate_github_url(source.get('filename', ''))
            
            cited_source = CitedSource(
                filename=source.get('filename', 'Unknown'),
                github_url=github_url,
                similarity_score=source.get('similarity_score', 0.0),
                content_snippet=source.get('content', '')[:500] + '...' if len(source.get('content', '')) > 500 else source.get('content', ''),
                line_numbers=source.get('line_numbers')
            )
            cited_sources.append(cited_source)
        
        session = QASession(
            question=question,
            answer=answer,
            provider=provider,
            timestamp=datetime.now().isoformat(),
            sources=cited_sources,
            performance_metrics=performance_metrics
        )
        
        self.sessions.append(session)
    
    def _generate_github_url(self, filename: str) -> Optional[str]:
        """Generate GitHub URL for a source file"""
        if not self.repo_url_base or not filename:
            return None
        
        # Clean filename path
        clean_filename = filename.lstrip('./')
        return f"{self.repo_url_base}/blob/main/{clean_filename}"
    
    def export_to_markdown(self, 
                          title: str = "SageVault Q&A Session Export",
                          include_performance: bool = True,
                          include_metadata: bool = True) -> str:
        """Export all sessions to a comprehensive Markdown document"""
        
        md_content = []
        
        # Header
        md_content.append(f"# {title}")
        md_content.append(f"*Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}*")
        md_content.append("")
        
        if include_metadata:
            md_content.extend(self._generate_metadata_section())
        
        # Table of Contents
        if len(self.sessions) > 1:
            md_content.append("## 📚 Table of Contents")
            for i, session in enumerate(self.sessions, 1):
                question_preview = session.question[:60] + "..." if len(session.question) > 60 else session.question
                md_content.append(f"{i}. [{question_preview}](#qa-session-{i})")
            md_content.append("")
        
        # Q&A Sessions
        for i, session in enumerate(self.sessions, 1):
            md_content.extend(self._format_session(session, i, include_performance))
        
        # Footer
        md_content.append("---")
        md_content.append("*Exported from SageVault - Intelligent Repository Explorer*")
        md_content.append("")
        
        return "\n".join(md_content)
    
    def _generate_metadata_section(self) -> List[str]:
        """Generate metadata section with session statistics"""
        total_sessions = len(self.sessions)
        providers_used = list(set(session.provider for session in self.sessions))
        total_sources = sum(len(session.sources) for session in self.sessions)
        
        metadata = [
            "## 📊 Session Statistics",
            "",
            f"- **Total Q&A Sessions**: {total_sessions}",
            f"- **LLM Providers Used**: {', '.join(providers_used)}",
            f"- **Total Sources Cited**: {total_sources}",
        ]
        
        if self.repo_url_base:
            metadata.append(f"- **Repository**: [{self.repo_url_base}]({self.repo_url_base})")
        
        metadata.extend(["", "---", ""])
        return metadata
    
    def _format_session(self, session: QASession, session_num: int, include_performance: bool) -> List[str]:
        """Format a single Q&A session as Markdown"""
        md_lines = []
        
        # Session header
        md_lines.append(f"## Q&A Session {session_num}")
        md_lines.append("")
        
        # Question
        md_lines.append("### ❓ Question")
        md_lines.append(f"> {session.question}")
        md_lines.append("")
        
        # Provider and timestamp
        session_time = datetime.fromisoformat(session.timestamp).strftime('%I:%M %p')
        # Proper capitalization for provider names
        provider_display = {
            'openai': 'OpenAI',
            'anthropic': 'Anthropic', 
            'google': 'Google',
            'groq': 'Groq'
        }.get(session.provider, session.provider.title())
        
        md_lines.append(f"**Provider**: {provider_display} | **Time**: {session_time}")
        
        # Performance metrics
        if include_performance and session.performance_metrics:
            metrics = session.performance_metrics
            if 'latency_ms' in metrics:
                perf_badge = f"⚡ {metrics['latency_ms']}ms"
                if 'tokens_in' in metrics and 'tokens_out' in metrics:
                    perf_badge += f" | 📊 {metrics['tokens_in']}↗/{metrics['tokens_out']}↘"
                if 'estimated_cost' in metrics:
                    perf_badge += f" | 💰 ${metrics['estimated_cost']:.3f}"
                md_lines.append(f"**Performance**: {perf_badge}")
        
        md_lines.append("")
        
        # Answer
        md_lines.append("### ✅ Answer")
        md_lines.append(session.answer)
        md_lines.append("")
        
        # Sources
        if session.sources:
            md_lines.append("### 📚 Sources & Citations")
            md_lines.append("")
            
            for i, source in enumerate(session.sources, 1):
                md_lines.extend(self._format_source(source, i))
        
        md_lines.append("---")
        md_lines.append("")
        
        return md_lines
    
    def _format_source(self, source: CitedSource, source_num: int) -> List[str]:
        """Format a single source citation"""
        lines = []
        
        # Source header with similarity score
        similarity_bar = "🟩" * min(int(source.similarity_score * 10), 10)
        similarity_pct = f"{source.similarity_score * 100:.1f}%"
        
        if source.github_url:
            lines.append(f"#### {source_num}. [{source.filename}]({source.github_url}) `{similarity_pct}` {similarity_bar}")
        else:
            lines.append(f"#### {source_num}. `{source.filename}` `{similarity_pct}` {similarity_bar}")
        
        if source.line_numbers:
            lines.append(f"*Lines {source.line_numbers}*")
        
        lines.append("")
        
        # Content snippet
        if source.content_snippet:
            lines.append("```")
            lines.append(source.content_snippet)
            lines.append("```")
        
        lines.append("")
        return lines
    
    def save_to_file(self, 
                    filename: str = None, 
                    title: str = "SageVault Q&A Session Export") -> str:
        """Save the markdown export to a file"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"sagevault_session_{timestamp}.md"
        
        markdown_content = self.export_to_markdown(title)
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        return filename
    
    def clear_sessions(self):
        """Clear all stored sessions"""
        self.sessions.clear()

# Global session exporter instance
session_exporter = SessionExporter()

# Example usage:
"""
# Set repository URL
session_exporter.set_repository_url("https://github.com/user/repo")

# Add a Q&A session
session_exporter.add_session(
    question="How does the authentication system work?",
    answer="The authentication system uses JWT tokens...",
    provider="openai",
    sources=[
        {
            'filename': 'src/auth/auth.py',
            'similarity_score': 0.85,
            'content': 'def authenticate_user(token):\n    # JWT validation logic...',
            'line_numbers': '15-45'
        }
    ],
    performance_metrics={'latency_ms': 1200, 'tokens_in': 1300, 'tokens_out': 600, 'estimated_cost': 0.002}
)

# Export to markdown
markdown = session_exporter.export_to_markdown()
filename = session_exporter.save_to_file()
"""