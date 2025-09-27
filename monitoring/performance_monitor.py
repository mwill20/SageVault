"""
🚀 SageVault Performance Monitor
Advanced provider cost/latency tracking with detailed metrics and cost estimation.
"""

import time
import json
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from functools import wraps

@dataclass
class ProviderMetrics:
    """Metrics for a single LLM provider request"""
    provider: str
    latency_ms: float
    tokens_in: Optional[int] = None
    tokens_out: Optional[int] = None
    estimated_cost: Optional[float] = None
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

class PerformanceMonitor:
    """
    Advanced performance monitoring for LLM providers
    Tracks latency, token usage, and cost estimates
    """
    
    # Provider pricing (per 1M tokens) - as of Sept 2025
    PROVIDER_COSTS = {
        'groq': {'input': 0.59, 'output': 0.79},  # Llama-3.1-8b-instant
        'openai': {'input': 0.150, 'output': 0.600},  # GPT-4o-mini
        'anthropic': {'input': 3.0, 'output': 15.0},  # Claude-3-5-sonnet
        'google': {'input': 0.075, 'output': 0.30},  # Gemini-1.5-flash
    }
    
    def __init__(self):
        self.metrics: Dict[str, list] = {}
        self.session_start = time.time()
    
    def track_request(self, provider: str):
        """Decorator to track provider request performance"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                
                try:
                    result = func(*args, **kwargs)
                    latency = (time.time() - start_time) * 1000  # Convert to ms
                    
                    # Extract token usage if available in result
                    tokens_in, tokens_out = self._extract_token_usage(result, provider)
                    
                    # Calculate estimated cost
                    cost = self._calculate_cost(provider, tokens_in, tokens_out)
                    
                    # Store metrics
                    metric = ProviderMetrics(
                        provider=provider,
                        latency_ms=round(latency, 1),
                        tokens_in=tokens_in,
                        tokens_out=tokens_out,
                        estimated_cost=cost
                    )
                    
                    self._store_metric(metric)
                    return result
                    
                except Exception as e:
                    # Still track failed requests
                    latency = (time.time() - start_time) * 1000
                    metric = ProviderMetrics(
                        provider=provider,
                        latency_ms=round(latency, 1)
                    )
                    self._store_metric(metric)
                    raise e
                    
            return wrapper
        return decorator
    
    def _extract_token_usage(self, result: Any, provider: str) -> tuple[Optional[int], Optional[int]]:
        """Extract token usage from LLM response"""
        try:
            if hasattr(result, 'usage'):
                # OpenAI format
                usage = result.usage
                return getattr(usage, 'prompt_tokens', None), getattr(usage, 'completion_tokens', None)
            elif hasattr(result, 'token_count'):
                # Google Gemini format
                return getattr(result, 'input_token_count', None), getattr(result, 'output_token_count', None)
            elif hasattr(result, 'meta') and 'tokens' in result.meta:
                # Anthropic format
                tokens = result.meta['tokens']
                return tokens.get('input_tokens'), tokens.get('output_tokens')
            elif provider == 'groq' and hasattr(result, 'x_groq'):
                # Groq specific usage
                usage = result.x_groq.get('usage', {})
                return usage.get('prompt_tokens'), usage.get('completion_tokens')
        except:
            pass
        
        return None, None
    
    def _calculate_cost(self, provider: str, tokens_in: Optional[int], tokens_out: Optional[int]) -> Optional[float]:
        """Calculate estimated cost based on token usage"""
        if not tokens_in or not tokens_out or provider not in self.PROVIDER_COSTS:
            return None
        
        costs = self.PROVIDER_COSTS[provider]
        cost = (tokens_in * costs['input'] + tokens_out * costs['output']) / 1_000_000
        return round(cost, 4)
    
    def _store_metric(self, metric: ProviderMetrics):
        """Store metric in session history"""
        if metric.provider not in self.metrics:
            self.metrics[metric.provider] = []
        self.metrics[metric.provider].append(metric)
    
    def get_provider_badge(self, provider: str) -> str:
        """Generate compact badge string for provider performance"""
        if provider not in self.metrics or not self.metrics[provider]:
            return f"{provider.capitalize()}: No data"
        
        latest = self.metrics[provider][-1]
        # Proper capitalization for provider names
        provider_display = {
            'openai': 'OpenAI',
            'anthropic': 'Anthropic', 
            'google': 'Google',
            'groq': 'Groq'
        }.get(provider, provider.title())
        
        badge_parts = [f"{provider_display}: {latest.latency_ms}ms"]
        
        if latest.tokens_in and latest.tokens_out:
            badge_parts.append(f"~{latest.tokens_in}↗/{latest.tokens_out}↘")
        
        if latest.estimated_cost:
            badge_parts.append(f"${latest.estimated_cost:.3f}")
        
        return ", ".join(badge_parts)
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get comprehensive session performance summary"""
        summary = {
            'session_duration_minutes': round((time.time() - self.session_start) / 60, 1),
            'providers': {}
        }
        
        for provider, metrics_list in self.metrics.items():
            if not metrics_list:
                continue
                
            latencies = [m.latency_ms for m in metrics_list]
            costs = [m.estimated_cost for m in metrics_list if m.estimated_cost]
            total_tokens_in = sum(m.tokens_in for m in metrics_list if m.tokens_in)
            total_tokens_out = sum(m.tokens_out for m in metrics_list if m.tokens_out)
            
            summary['providers'][provider] = {
                'requests': len(metrics_list),
                'avg_latency_ms': round(sum(latencies) / len(latencies), 1),
                'min_latency_ms': round(min(latencies), 1),
                'max_latency_ms': round(max(latencies), 1),
                'total_cost': round(sum(costs), 4) if costs else None,
                'total_tokens_in': total_tokens_in if total_tokens_in > 0 else None,
                'total_tokens_out': total_tokens_out if total_tokens_out > 0 else None,
            }
        
        return summary
    
    def export_metrics(self) -> str:
        """Export all metrics as JSON string"""
        export_data = {
            'session_summary': self.get_session_summary(),
            'detailed_metrics': {}
        }
        
        for provider, metrics_list in self.metrics.items():
            export_data['detailed_metrics'][provider] = [
                asdict(metric) for metric in metrics_list
            ]
        
        return json.dumps(export_data, indent=2)

# Global performance monitor instance
performance_monitor = PerformanceMonitor()

def track_llm_request(provider: str):
    """Convenience decorator for tracking LLM requests"""
    return performance_monitor.track_request(provider)

# Example usage:
"""
@track_llm_request('openai')
def call_openai_api(prompt: str):
    # Your OpenAI API call here
    return client.chat.completions.create(...)

# Get badge for UI display
badge = performance_monitor.get_provider_badge('openai')
# Returns: "OpenAI: 1.2s, ~1.3k↗/600↘, $0.002"
"""