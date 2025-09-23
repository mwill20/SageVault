from __future__ import annotations
from typing import List, Dict, Any

# Use explicit relative imports to match package style elsewhere.
from .security_utils import (
    penalize_suspicious,
    redact_secrets,
    sanitize_text,
)
from .security_utils import warn  # warn is a UI helper that wraps st.warning


def secure_text(text: str | None) -> str:
    """Sanitize, redact, risk-evaluate a free-form text snippet (idempotent).

    Order adjusted for better redaction & stability:
    1. Coerce None -> ''.
    2. Redact secrets on raw (pre-escape) to improve pattern matches.
    3. Sanitize (HTML-escape + markdown neutralization) exactly once.
    4. Score via penalize_suspicious (wrapped as dict) and surface warning.
    5. Return escaped, redacted, stable string. Re-running does not double-escape.
    """
    raw = text or ""
    redacted = redact_secrets(raw)  # redact before escaping to catch tokens like sk-xxx
    cleaned = sanitize_text(redacted)
    scored = penalize_suspicious({"cmd": cleaned})
    if isinstance(scored, dict) and scored.get("warning"):
        warn(scored["warning"])
    return (scored.get("cmd") if isinstance(scored, dict) else cleaned)  # type: ignore[arg-type]


def secure_plan(steps: List[Dict[str, Any]] | None) -> List[Dict[str, Any]]:
    """Apply sanitization, redaction, and risk scoring to a plan structure.

    Each step is expected to have optional keys: title, why, cmd, cite, risk.
    - Sanitizes textual fields (title/why/cmd) prior to redaction & scoring.
    - Redacts secrets in command strings.
    - Uses penalize_suspicious on a dict payload so scoring logic can inspect
      multiple fields (title/why/cmd). This relies on the polymorphic behavior
      implemented in security_utils.
    - Propagates warning & normalized risk back onto the step.

    Returns a NEW list of secured step dicts (original input is not mutated).
    """
    if not steps:
        return []
    secured: List[Dict[str, Any]] = []
    for s in steps:
        s2 = dict(s)
        raw_title = str(s2.get("title", ""))
        raw_why = str(s2.get("why", ""))
        raw_cmd = str(s2.get("cmd", ""))

        # Redact before escaping
        red_title = redact_secrets(raw_title)
        red_why = redact_secrets(raw_why)
        red_cmd = redact_secrets(raw_cmd)

        # Avoid double-escaping: detect already-escaped ampersands (&amp;)
        def _once(val: str) -> str:
            return val if "&amp;" in val else sanitize_text(val)
        title = _once(red_title)
        why = _once(red_why)
        cmd_escaped = _once(red_cmd)

        # Block / neutralize high-risk shell pipelines explicitly
        if "curl" in raw_cmd and "|" in raw_cmd and "sh" in raw_cmd:
            cmd_escaped = "# BLOCKED: risky curl pipe removed by security gate"
            s2["warning"] = s2.get("warning") or "Shell pipeline blocked (curl | sh). Review manually."
            # Explicitly raise baseline risk high
            s2["risk"] = max(float(s2.get("risk", 0.0)), 0.9)

        scored = penalize_suspicious({
            "title": title,
            "why": why,
            "cmd": cmd_escaped,
            "cite": s2.get("cite", []),
        })
        if isinstance(scored, dict):
            if scored.get("warning"):
                s2["warning"] = s2.get("warning") or scored["warning"]
            s2["cmd"] = scored.get("cmd", cmd_escaped)
            # Preserve any pre-set elevated risk
            combined_risk = max(float(scored.get("risk", 0.0)), float(s2.get("risk", 0.0)))
            s2["risk"] = min(max(combined_risk, 0.0), 1.0)
        else:
            s2["cmd"] = cmd_escaped
            s2.setdefault("risk", 0.0)
        s2["title"] = title
        s2["why"] = why
        secured.append(s2)
    return secured
