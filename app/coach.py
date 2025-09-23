# app/coach.py
from __future__ import annotations
import streamlit as st
from typing import List, Dict, Any
from .planner import extract_repo_signals, plan_walkthrough, PlanStep
from .security_utils import injection_score
from .security_gate import secure_plan, secure_text


def warn(msg: str) -> None:
    """Local warning helper (UI standard)."""
    st.warning(msg, icon="⚠️")

def _chip_row(labels: list[str]) -> None:
    if not labels: 
        st.caption("Citations: –")
        return
    st.caption("Citations: " + " · ".join(f"`{c}`" for c in labels))

def render_coach_page(repo_root: str = ".") -> None:
    # --- Signals + Plan ---
    sig = extract_repo_signals(repo_root)
    raw_plan: List[PlanStep] = plan_walkthrough(sig)

    # Build raw dict steps first (coach retains existing heuristic injection_score for transparency)
    proto_steps: List[Dict[str, Any]] = []
    for s in raw_plan:
        inj_hits = sum(injection_score(f or "") for f in (s.title, s.why, s.cmd))
        if inj_hits:
            warn(f"Potential risky pattern in step '{s.id}' (heuristic matches: {inj_hits}). Review the command before executing.")
        proto_steps.append({
            "id": s.id,
            "title": s.title,
            "why": s.why,
            "cmd": s.cmd or "",
            "cite": s.cite,
            "risk": s.risk,
            "inj_score": inj_hits,
        })

    # Pass through unified security gate (sanitization, redaction, risk normalization)
    secured = secure_plan(proto_steps)
    # Merge back injection score (secure_plan may adjust risk/warning but doesn't know inj_score)
    inj_index = {s["id"]: s.get("inj_score") for s in proto_steps}
    safe_steps: List[Dict[str, Any]] = []
    for s in secured:
        s["inj_score"] = inj_index.get(s.get("id"), s.get("inj_score"))
        safe_steps.append(s)

    # Persist for reuse
    st.session_state["last_signals"] = sig
    st.session_state["last_plan"] = safe_steps

    # --- UI ---
    st.title("Coach Mode")
    c_head1, c_head2 = st.columns([6,1])
    with c_head1:
        st.write("Step-by-step walkthrough with safety rails and citations.")
    with c_head2:
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

    if not safe_steps:
        st.info("No walkthrough steps generated for this repository.")
        return

    # Optional future user note echo (placeholder demonstrating secure_text usage)
    # user_note = st.text_area("Notes (local only, not persisted)")
    # if user_note:
    #     st.caption("Sanitized note:")
    #     st.write(secure_text(user_note))

    # Checklist
    for ix, step in enumerate(safe_steps, 1):
        box = st.container(border=True)
        with box:
            header = f"**{ix}. {step['title']}**"
            badges = []
            if float(step.get("risk", 0)) >= 0.5:
                badges.append("⚠️ risk")
            if step.get("inj_score"):
                badges.append(f"heuristic {step['inj_score']}")
            if badges:
                header += "  " + " ".join(badges)
            st.markdown(header)
            st.caption(step["why"])
            _chip_row(step.get("cite", []))
            if step.get("cmd"):
                st.code(step["cmd"], language="bash")
