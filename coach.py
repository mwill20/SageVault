# coach.py — flat imports, no relative/package imports
from __future__ import annotations
from typing import List, Dict, Any
import streamlit as st

from planner import extract_repo_signals, plan_walkthrough, PlanStep
from security_gate import secure_plan

def _chip_row(labels: list[str]) -> None:
    if not labels:
        st.caption("Citations: –")
        return
    chips = " · ".join(f"`{c}`" for c in labels)
    st.caption(f"Citations: {chips}")

def render_coach_page(repo_root: str = ".") -> None:
    # Build signals + plan
    sig = extract_repo_signals(repo_root)
    raw_plan: List[PlanStep] = plan_walkthrough(sig)

    # Safety gate (adds risk/warning, redacts cmd)
    steps_dicts: List[Dict[str, Any]] = [
        {"title": s.title, "why": s.why, "cmd": (s.cmd or ""), "cite": s.cite, "risk": float(s.risk)}
        for s in raw_plan
    ]
    safe_steps = secure_plan(steps_dicts)

    # Persist for Repo Tour
    st.session_state["last_signals"] = sig
    st.session_state["last_plan"] = safe_steps

    # Header
    st.subheader("Coach Mode")
    col1, col2 = st.columns([6, 1])
    with col1:
        st.write("Step-by-step walkthrough with safety rails and citations.")
    with col2:
        if st.button("Regenerate"):
            st.rerun()

    # Sidebar: Signals
    with st.sidebar:
        st.subheader("Repo Signals")
        st.write({
            "readme": sig.readme_path,
            "deps": sig.deps,
            "entrypoint": sig.entrypoint,
            "lang": sig.lang
        })

    # Checklist (simple, no fancy containers)
    for ix, step in enumerate(safe_steps, start=1):
        risky = float(step.get("risk", 0.0)) >= 0.5
        title = f"**{ix}. {step['title']}**" + ("  ⚠️" if risky else "")
        st.markdown(title)
        st.write(step.get("why", ""))
        _chip_row(step.get("cite", []))
        cmd = step.get("cmd", "")
        if cmd:
            st.code(cmd, language="bash")
        st.markdown("---")
