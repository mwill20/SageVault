# memory_orchestrator.py
"""Hierarchical context assembly: episodic -> window -> summary fallback.

Simplistic implementation; can evolve to track token estimates, decisions ledger, etc.
"""
from __future__ import annotations
from typing import List, Dict, Any

# Placeholder hit structure expectation: {"path": str, "chunk": int, "text": str, "similarity": float}

def _tok_estimate(s: str) -> int:
    # Rough heuristic (~4 chars per token)
    return max(1, len(s) // 4)

def format_hits(hits: List[Dict[str, Any]], limit_chars: int | None = None) -> str:
    parts = []
    for h in hits:
        txt = h.get("text", "").strip()
        if limit_chars and len(txt) > limit_chars:
            txt = txt[:limit_chars].rsplit(" ", 1)[0] + " …"
        parts.append(f"File: {h.get('path')} (chunk {h.get('chunk')})\n{txt}")
    return "\n\n".join(parts)

def format_window(turns: List[tuple], max_turns: int = 6) -> str:
    # turns: list of (question, answer)
    tail = turns[-max_turns:]
    segs = []
    for q, a in tail:
        segs.append(f"Q: {q}\nA: {a[:800]}")
    return "\n\n".join(segs)

def assemble_context(query: str,
                     episodic_hits: List[Dict[str, Any]],
                     window_turns: List[tuple],
                     summary_digest: str,
                     cfg: Dict[str, Any],
                     ledger: List[str] | None = None) -> str:
    max_tokens = cfg.get("policy", {}).get("max_ctx_tokens", 3000)
    parts: List[str] = []
    token_used = 0
    def add(segment: str):
        nonlocal token_used
        if not segment: return
        est = _tok_estimate(segment)
        if token_used + est > max_tokens:
            return
        parts.append(segment)
        token_used += est

    # 1) Episodic (retrieval) always first
    add(format_hits(episodic_hits, limit_chars=1200))

    # 2) Coverage heuristic
    q_terms = {w.lower() for w in query.split() if len(w) > 3}
    coverage = any(any(t in h.get("text", "").lower() for t in q_terms) for h in episodic_hits)

    if not coverage:
        add(format_window(window_turns))

    # 3) If still under budget & have ledger facts, add concise ledger first
    if ledger:
        add("Ledger:\n" + "\n".join(ledger[-8:]))
    # 4) Then summary digest if still space
    if token_used < max_tokens * 0.6 and summary_digest:
        add(summary_digest[:1200])

    # If we somehow exceeded (shouldn't), clip final join
    joined = "\n\n".join(parts)
    # Hard char cap as a final safeguard (approx tokens*4)
    char_cap = max_tokens * 4
    if len(joined) > char_cap:
        joined = joined[:char_cap].rsplit(" ", 1)[0] + " …"
    return joined

def update_ledger(ledger: List[str], question: str, answer: str) -> List[str]:
    """Append a compact fact entry (redacted). Keep last 25."""
    from .security_utils import redact_secrets
    q = question.replace("\n", " ")[:120]
    a = redact_secrets(answer.replace("\n", " ")[:160])
    ledger.append(f"- Q: {q} | A: {a}")
    return ledger[-25:]

__all__ = ["assemble_context", "format_hits", "format_window", "update_ledger"]
