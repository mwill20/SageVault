# security_gate.py — flat imports (no leading dots)
from __future__ import annotations
from typing import List, Dict, Any

# Use the helpers already in security_utils.py (no relative import)
from security_utils import penalize_suspicious, redact_secrets, warn

def secure_text(text: str) -> str:
    txt = redact_secrets(text or "")
    scored = penalize_suspicious({"cmd": txt})
    if scored.get("warning"):
        warn(scored["warning"])
    # prefer any sanitized/modified cmd from the scorer
    return scored.get("cmd", txt)

def secure_plan(steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    secured: List[Dict[str, Any]] = []
    for s in steps:
        s2 = dict(s)
        # redact and score command
        cmd = redact_secrets(s2.get("cmd") or "")
        scored = penalize_suspicious({
            "title": s2.get("title", ""),
            "why": s2.get("why", ""),
            "cmd": cmd,
            "cite": s2.get("cite", []),
        })
        if scored.get("warning"):
            warn(scored["warning"])
        s2["cmd"] = scored.get("cmd", cmd)
        s2["risk"] = float(scored.get("risk", s2.get("risk", 0.0)))
        s2["warning"] = scored.get("warning", s2.get("warning"))
        secured.append(s2)
    return secured
