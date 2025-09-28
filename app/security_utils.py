# security_utils.py
"""Security & hygiene helpers (deterministic, outside model prompt).

Functions here are lightweight and safe to call inline. Heavier ML
classifiers can be added later behind the same interfaces.
"""
from __future__ import annotations

import html
import posixpath
import re
from typing import Any, Dict, List

# ──────────────────────────────────────────────────────────────────────────────
# Basic regex/pattern hygiene
# ──────────────────────────────────────────────────────────────────────────────
_CTRL = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F]")
_MD_LINK = re.compile(r"\[([^\]]{1,80})\]\(([^)]+)\)")
_SECRET = re.compile(
    r"(?:sk-[A-Za-z0-9]{4,}|ghp_[A-Za-z0-9]{36}|AKIA[0-9A-Z]{16}|eyJhbGciOi|AIza[0-9A-Za-z_-]{35})"
)
_DANGEROUS = (
    "git push --force",
    "rm -rf",
    "curl | bash",
    "curl | sh", 
    "chmod 777",
    "| bash",
    "| sh",
)

# Injection heuristic patterns (compiled case-insensitive)
INJECTION_PATTERNS = [
    r"ignore\s+(all|any|previous|above)\s+(instructions|context|prompt)",
    r"reveal\s+system\s+prompt",
    r"\bas\s*system\b",
    r"escalate\s+privileges",
    r"\brm\s+-rf\s+/?",
    r"curl\s+[^|]+\|\s*(sh|bash)",
    r"disable\s+\w*\s*safety",
    r"tell\s+me\s+secrets?",
    r"show\s+(all|me)\s+(secrets?|keys?|credentials?)",
]
INJECTION_REGEXES = [re.compile(p, re.I) for p in INJECTION_PATTERNS]

_DEF_MAX_LEN = 2000


# ──────────────────────────────────────────────────────────────────────────────
# Sanitization & Redaction
# ──────────────────────────────────────────────────────────────────────────────
def sanitize_text(s: str | None, max_len: int = _DEF_MAX_LEN) -> str:
    """Strip control chars, neutralize markdown links, HTML-escape (UI safety)."""
    if not s:
        return ""
    s = _CTRL.sub("", s)
    s = _MD_LINK.sub(r"\1 (\2)", s)  # [text](url) → text (url)
    return html.escape(s.strip())[:max_len]


def redact_secrets(s: str | None) -> str:
    """Replace common key/token patterns with [REDACTED]."""
    if not s:
        return ""
    return _SECRET.sub("[REDACTED]", s)


def normalize_repo_path(p: str) -> str:
    """Normalize and prevent path traversal; return '' if unsafe."""
    p = (p or "").replace("\\", "/")
    safe = posixpath.normpath("/" + p).lstrip("/")
    return "" if safe.startswith("..") else safe


# ──────────────────────────────────────────────────────────────────────────────
# Dangerous command labeling (plain-text, simple heuristics)
# ──────────────────────────────────────────────────────────────────────────────
def label_dangerous_commands(text: str) -> str:
    """Insert WARN: lines above dangerous commands; avoids duplicates."""
    if not text:
        return ""
    lines = text.splitlines()
    out: List[str] = []
    for line in lines:
        raw = line.strip()
        if any(d in raw for d in _DANGEROUS):
            if not (out and out[-1].startswith("**WARN:**")):
                out.append("**WARN:** High-risk command detected; consider safer alternative (e.g., --force-with-lease or backup first).")
        out.append(line)
    return "\n".join(out)


def extract_dangerous(text: str) -> List[str]:
    """Return a list of dangerous substrings found."""
    if not text:
        return []
    return [d for d in _DANGEROUS if d in text]


def warn_dangerous(cmd: str) -> str:
    """Backward-compatible wrapper for single/multi-line strings."""
    return label_dangerous_commands(cmd)


# ──────────────────────────────────────────────────────────────────────────────
# Injection heuristics
# ──────────────────────────────────────────────────────────────────────────────
def injection_score(text: str) -> int:
    """Return integer count of matched injection patterns (>=1 for obvious attacks)."""
    if not text:
        return 0
    return sum(1 for rx in INJECTION_REGEXES if rx.search(text))


def _extract_text(item: Any, text_key: str = "text") -> str:
    """Get textual content from dicts/objects; fallback to str(item)."""
    if isinstance(item, dict):
        return str(item.get(text_key, ""))
    txt = getattr(item, "text", None)
    return str(txt) if txt is not None else str(item)


def _extract_attr(item: Any, key: str, default: Any = None):
    if isinstance(item, dict):
        return item.get(key, default)
    return getattr(item, key, default)


def _coerce_hit(
    item: Any,
    text_key: str = "text",
    path_key: str = "path",
    similarity_key: str = "similarity",
) -> Dict[str, Any]:
    """Normalize an item (dict/object) → dict with text/path/similarity."""
    text = _extract_attr(item, text_key, "")
    path = _extract_attr(item, path_key, _extract_attr(item, "file", ""))
    sim = _extract_attr(item, similarity_key, 1.0)
    try:
        sim = float(sim)
    except Exception:
        sim = 1.0
    return {"text": str(text or ""), "path": str(path or ""), "similarity": float(sim)}


def _matches_any(s: str | None) -> bool:
    if not s:
        return False
    return any(rx.search(s) for rx in INJECTION_REGEXES)


def penalize_suspicious(
    payload: Any,
    text_key: str = "text",
    max_share: float | None = None,
) -> Any:
    """
    Polymorphic safety pass.

    • If `payload` is a list (retrieval hits): stable-sort by injection risk (safer first)
      and reduce similarity for risky hits. Returns list of dicts:
      {"text","path","similarity"} for test compatibility.

    • If `payload` is a dict (Coach Mode step): attach/raise `risk` and optional `warning`
      based on command and text injection signals. Returns a dict.
    """
    # List path (existing behavior)
    if isinstance(payload, list):
        if not payload:
            return []
        coerced = [_coerce_hit(d, text_key=text_key) for d in payload]
        scored: List[Dict[str, Any]] = []
        for h in coerced:
            s = injection_score(h["text"])
            penalty = 1.0 / (1.0 + s)  # s=0 → 1.0; s>=1 → <1.0
            h2 = dict(h)
            h2["similarity"] = float(h2["similarity"]) * penalty
            h2["_inj_score"] = s  # for sorting only
            scored.append(h2)
        scored.sort(key=lambda x: x["_inj_score"])  # safer first
        for h in scored:
            h.pop("_inj_score", None)
        return scored

    # Dict path (Coach Mode step)
    if isinstance(payload, dict):
        out = dict(payload)
        title = str(out.get("title", ""))
        why = str(out.get("why", ""))
        cmd = str(out.get("cmd", "") or "")
        # Base risk nonzero to avoid "zero-risk" illusions
        risk = float(out.get("risk", 0.1))

        # Raise risk on detected injection-like text or dangerous pipelines
        inj = injection_score(" ".join([title, why, cmd]))
        if inj >= 1:
            risk = max(risk, 0.6)
        if re.search(r"curl\s+[^|]+\|\s*sh", cmd, flags=re.I) or re.search(r"rm\s+-rf\s+/?", cmd, flags=re.I):
            risk = max(risk, 0.9)
            out["warning"] = "Suspicious shell pipeline detected. Review before running."

        out["risk"] = min(max(risk, 0.0), 1.0)
        return out

    # Fallback: return as-is
    return payload


def diversity_guard(items: List[dict], key: str = "path", max_per_key: int = 2) -> List[dict]:
    """Limit how many items share the same `key` value; preserve order."""
    if not items:
        return []
    seen: Dict[Any, int] = {}
    out: List[dict] = []
    for it in items:
        v = it.get(key)
        cnt = seen.get(v, 0)
        if cnt < max_per_key:
            out.append(it)
            seen[v] = cnt + 1
    return out


# ──────────────────────────────────────────────────────────────────────────────
# Token counting (rough, provider-agnostic placeholder)
# ──────────────────────────────────────────────────────────────────────────────
def count_tokens_rough(s: str) -> int:
    return max(1, len(s) // 4) if s else 1


def count_tokens_provider(messages: List[dict], provider: str = "openai:gpt-4o-mini") -> int:
    return sum(count_tokens_rough(m.get("content", "")) for m in messages)


# ──────────────────────────────────────────────────────────────────────────────
# Streamlit-aware warn helper (no-op outside Streamlit)
# ──────────────────────────────────────────────────────────────────────────────
def warn(msg: str) -> None:
    try:
        import streamlit as st  # type: ignore
        st.warning(msg)
    except Exception:
        # Silent no-op when Streamlit isn't available (tests/CLI)
        pass


__all__ = [
    "sanitize_text",
    "redact_secrets",
    "normalize_repo_path",
    "label_dangerous_commands",
    "extract_dangerous",
    "warn_dangerous",
    "injection_score",
    "penalize_suspicious",
    "diversity_guard",
    "count_tokens_rough",
    "count_tokens_provider",
    "warn",
]
