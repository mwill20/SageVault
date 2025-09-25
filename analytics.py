"""Privacy-First Analytics for SageVault

Minimal, ephemeral analytics tracking with zero PII collection.
Tracks only aggregate usage metrics: counts and timestamps.
No user data, prompts, API keys, or source content stored.
"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import os

@dataclass
class AnalyticsEvent:
    """Single analytics event with minimal data"""
    event_type: str
    timestamp: float
    count: int = 1
    metadata: Optional[Dict] = None

class PrivacyFirstAnalytics:
    """Ephemeral analytics with strict privacy controls"""
    
    def __init__(self, session_id: Optional[str] = None):
        """Initialize analytics with session-scoped storage"""
        self.session_id = session_id or f"session_{int(time.time())}"
        self.events: List[AnalyticsEvent] = []
        self.session_start = time.time()
        
        # Define allowed event types (prevent arbitrary data collection)
        self.ALLOWED_EVENTS = {
            'index_built',
            'question_asked', 
            'files_included',
            'files_excluded',
            'app_started',
            'llm_response_generated',
            'security_override_triggered',
            'document_uploaded'
        }
    
    def track_event(self, event_type: str, count: int = 1, metadata: Dict = None) -> bool:
        """Track an analytics event with privacy safeguards"""
        # Validate event type
        if event_type not in self.ALLOWED_EVENTS:
            return False
            
        # Sanitize metadata to prevent PII leakage
        safe_metadata = self._sanitize_metadata(metadata or {})
        
        # Create event
        event = AnalyticsEvent(
            event_type=event_type,
            timestamp=time.time(),
            count=count,
            metadata=safe_metadata
        )
        
        self.events.append(event)
        return True
    
    def _sanitize_metadata(self, metadata: Dict) -> Dict:
        """Remove any potentially sensitive data from metadata"""
        safe_metadata = {}
        
        # Only allow specific safe keys
        SAFE_KEYS = {
            'file_count', 'provider_type', 'chunk_size', 'overlap_percent',
            'file_types', 'risk_level', 'source_type', 'error_type'
        }
        
        for key, value in metadata.items():
            if key in SAFE_KEYS:
                # Ensure values are non-PII
                if isinstance(value, (int, float, bool)):
                    safe_metadata[key] = value
                elif isinstance(value, str) and len(value) < 50:
                    # Only short, categorical strings
                    safe_metadata[key] = value
                elif isinstance(value, list) and all(isinstance(x, str) for x in value):
                    # File extensions or types only
                    safe_metadata[key] = value[:10]  # Limit to 10 items
        
        return safe_metadata
    
    def get_session_stats(self) -> Dict:
        """Get aggregated session statistics"""
        if not self.events:
            return {"session_id": self.session_id, "events": 0, "duration": 0}
        
        # Calculate session duration
        duration = time.time() - self.session_start
        
        # Aggregate events by type
        event_counts = {}
        for event in self.events:
            event_counts[event.event_type] = event_counts.get(event.event_type, 0) + event.count
        
        # Calculate totals
        total_files_processed = (
            event_counts.get('files_included', 0) + 
            event_counts.get('files_excluded', 0)
        )
        
        return {
            "session_id": self.session_id,
            "session_duration_minutes": round(duration / 60, 1),
            "total_events": len(self.events),
            "event_counts": event_counts,
            "total_files_processed": total_files_processed,
            "questions_asked": event_counts.get('question_asked', 0),
            "indexes_built": event_counts.get('index_built', 0),
            "security_overrides": event_counts.get('security_override_triggered', 0)
        }
    
    def export_session_log(self, include_timestamps: bool = False) -> str:
        """Export session analytics as JSON string"""
        if include_timestamps:
            # Include individual events with timestamps
            export_data = {
                "session_id": self.session_id,
                "session_start": datetime.fromtimestamp(self.session_start).isoformat(),
                "events": [asdict(event) for event in self.events],
                "summary": self.get_session_stats()
            }
        else:
            # Only aggregated data
            export_data = self.get_session_stats()
        
        return json.dumps(export_data, indent=2, default=str)
    
    def clear_session(self):
        """Clear all analytics data for privacy"""
        self.events.clear()
        self.session_start = time.time()
    
    def get_recent_activity(self, minutes: int = 5) -> List[AnalyticsEvent]:
        """Get events from the last N minutes"""
        cutoff = time.time() - (minutes * 60)
        return [event for event in self.events if event.timestamp >= cutoff]
    
    def __len__(self) -> int:
        """Return number of tracked events"""
        return len(self.events)

# Global instance for session-scoped analytics
_session_analytics: Optional[PrivacyFirstAnalytics] = None

def get_analytics() -> PrivacyFirstAnalytics:
    """Get or create session analytics instance"""
    global _session_analytics
    if _session_analytics is None:
        _session_analytics = PrivacyFirstAnalytics()
        # Track app start
        _session_analytics.track_event('app_started')
    return _session_analytics

def track_index_built(file_count: int, file_types: List[str] = None, source_type: str = "repository"):
    """Track repository/document indexing completion"""
    analytics = get_analytics()
    metadata = {
        'file_count': file_count,
        'source_type': source_type
    }
    if file_types:
        # Only track file extensions, not full paths
        extensions = list(set([f.split('.')[-1] if '.' in f else 'no_ext' for f in file_types[:20]]))
        metadata['file_types'] = extensions
    
    analytics.track_event('index_built', metadata=metadata)

def track_question_asked(provider_type: str = None, response_generated: bool = True):
    """Track user question submission"""
    analytics = get_analytics()
    metadata = {}
    if provider_type:
        metadata['provider_type'] = provider_type
    
    analytics.track_event('question_asked', metadata=metadata)
    
    if response_generated:
        analytics.track_event('llm_response_generated', metadata=metadata)

def track_files_processed(included_count: int, excluded_count: int, risk_levels: List[str] = None):
    """Track file processing results"""
    analytics = get_analytics()
    
    if included_count > 0:
        analytics.track_event('files_included', count=included_count)
    
    if excluded_count > 0:
        metadata = {}
        if risk_levels:
            # Count risk levels without exposing file names
            risk_counts = {}
            for level in risk_levels:
                risk_counts[level] = risk_counts.get(level, 0) + 1
            metadata['risk_levels'] = risk_counts
        
        analytics.track_event('files_excluded', count=excluded_count, metadata=metadata)

def track_security_override(risk_level: str = None):
    """Track security override usage"""
    analytics = get_analytics()
    metadata = {}
    if risk_level:
        metadata['risk_level'] = risk_level
    
    analytics.track_event('security_override_triggered', metadata=metadata)

def track_document_upload(file_count: int, file_types: List[str] = None):
    """Track document upload events"""
    analytics = get_analytics()
    metadata = {'file_count': file_count}
    
    if file_types:
        # Only track extensions
        extensions = list(set([f.split('.')[-1] if '.' in f else 'unknown' for f in file_types[:10]]))
        metadata['file_types'] = extensions
    
    analytics.track_event('document_uploaded', metadata=metadata)

def get_session_summary() -> Dict:
    """Get current session analytics summary"""
    return get_analytics().get_session_stats()

def export_analytics(include_timestamps: bool = False) -> str:
    """Export analytics data as JSON"""
    return get_analytics().export_session_log(include_timestamps)

def clear_analytics():
    """Clear all analytics data"""
    global _session_analytics
    if _session_analytics:
        _session_analytics.clear_session()

# Privacy compliance functions
def get_privacy_info() -> Dict:
    """Get information about what data is collected"""
    return {
        "data_collected": {
            "event_types": list(PrivacyFirstAnalytics().__dict__.get('ALLOWED_EVENTS', [])),
            "data_points": ["event counts", "timestamps", "file counts", "provider types"],
            "retention": "session-only (cleared on restart)",
            "storage": "in-memory only"
        },
        "data_not_collected": [
            "user prompts or questions",
            "API keys or tokens", 
            "file contents or names",
            "repository URLs",
            "user identification",
            "IP addresses",
            "personal information"
        ],
        "compliance": {
            "gdpr_compliant": True,
            "ccpa_compliant": True,
            "data_minimization": True,
            "purpose_limitation": True
        }
    }