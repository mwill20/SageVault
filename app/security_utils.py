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

__all__ = [
    "sanitize_text",
    "redact_secrets",
    "normalize_repo_path",
    "label_dangerous_commands",
    "extract_dangerous",
]
