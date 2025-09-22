# security_utils.py
"""Security & hygiene helpers (deterministic, outside model prompt).

Functions here should be lightweight and safe to call inline. Heavy/ML
classifiers can be added later.
"""
from __future__ import annotations
import re, html, posixpath
from typing import Iterable, List, Tuple

# Basic regex patterns (extend as needed)
_CTRL = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F]")
_MD_LINK = re.compile(r"\[([^\]]{1,80})\]\(([^)]+)\)")
_SECRET = re.compile(r"(?:sk-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{36}|AKIA[0-9A-Z]{16}|eyJhbGciOi|AIza[0-9A-Za-z_-]{35})")
_DANGEROUS = (
    "git push --force",
    "rm -rf",
    "curl | bash",
    "chmod 777",
)

# Injection heuristic patterns (case-insensitive)
INJECTION_PATTERNS = [
    r"ignore (previous|earlier) instructions",
    r"reveal (your )?(system|hidden) prompt",
    r"bypass (safety|guard|policy)",
    r"disable (safety|filters)",
]

_DEF_MAX_LEN = 2000


def sanitize_text(s: str | None, max_len: int = _DEF_MAX_LEN) -> str:
    """Basic hygiene: strip control chars, neutralize markdown links, HTML-escape.
    Not for semantic fidelity—just UI safety & cleanliness.
    """
    if not s:
        return ""
    s = _CTRL.sub("", s)
    # Convert [text](url) -> text (url) to avoid hidden targets
    s = _MD_LINK.sub(r"\1 (\2)", s)
    return html.escape(s.strip())[:max_len]


def redact_secrets(s: str | None) -> str:
    if not s:
        return ""
    return _SECRET.sub("[REDACTED]", s)


def normalize_repo_path(p: str) -> str:
    p = (p or "").replace("\\", "/")
    # Anchor so normpath can't escape root, then strip leading slash we added
    safe = posixpath.normpath("/" + p).lstrip("/")
    # Disallow parent traversal remnants
    if safe.startswith(".."):
        return ""
    return safe


def label_dangerous_commands(text: str) -> str:
    """Insert WARN: lines above dangerous commands inside a fenced block if missing.
    Simple line-by-line scan; can be enhanced later with parsing.
    """
    if not text:
        return ""
    lines = text.splitlines()
    out: List[str] = []
    for i, line in enumerate(lines):
        raw = line.strip()
        if any(d in raw for d in _DANGEROUS):
            # Avoid duplicate warnings
            if not (out and out[-1].startswith("**WARN:**")):
                out.append("**WARN:** High-risk command detected; consider safer alternative (e.g., --force-with-lease or backup first).")
        out.append(line)
    return "\n".join(out)


def extract_dangerous(text: str) -> List[str]:
    found = []
    if not text:
        return found
    for d in _DANGEROUS:
        if d in text:
            found.append(d)
    return found

def warn_dangerous(cmd: str) -> str:
    """Backward-compatible helper: wraps a single command string and injects WARN if dangerous.
    If multiple lines provided, scans all lines (delegates to label_dangerous_commands)."""
    return label_dangerous_commands(cmd)


def injection_score(text: str) -> float:
    """Return a heuristic injection score in [0,1]."""
    if not text:
        return 0.0
    t = text.lower()
    hits = 0
    for p in INJECTION_PATTERNS:
        try:
            if re.search(p, t):
                hits += 1
        except re.error:
            continue
    if hits == 0:
        return 0.0
    return min(1.0, hits / 3.0)


def penalize_suspicious(hits: List[dict], max_share: float = 0.6) -> List[dict]:
    """Down-weight suspicious hits (mutates 'similarity' or 'score') & enforce diversity.

    Expects each hit to have keys: 'text', 'path', and either 'similarity' or 'score'.
    Returns filtered list where no single file exceeds max_share of retained hits.
    """
    if not hits:
        return hits
    by_file = {}
    for h in hits:
        inj = injection_score(h.get("text", ""))
        # Mutate similarity/score downwards if suspicious
        key = "similarity" if "similarity" in h else ("score" if "score" in h else None)
        if key:
            orig = h.get(key, 0.0)
            h[key] = orig * (1.0 - 0.5 * inj)
        path = h.get("path", "")
        by_file[path] = by_file.get(path, 0) + 1
    total = max(1, len(hits))
    filtered = [h for h in hits if (by_file.get(h.get("path", ""), 0) / total) <= max_share]
    # If filtering removed everything (e.g., one file dominated), fall back to original hits
    return filtered or hits


# Token counting (rough, provider-agnostic placeholder)
def count_tokens_rough(s: str) -> int:
    return max(1, len(s) // 4) if s else 1


def count_tokens_provider(messages: List[dict], provider: str = "openai:gpt-4o-mini") -> int:
    return sum(count_tokens_rough(m.get("content", "")) for m in messages)

__all__ = [
    "sanitize_text",
    "redact_secrets",
    "normalize_repo_path",
    "label_dangerous_commands",
    "extract_dangerous",
    "warn_dangerous",
    "injection_score",
    "penalize_suspicious",
    "count_tokens_rough",
    "count_tokens_provider",
]
