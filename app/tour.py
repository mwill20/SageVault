from __future__ import annotations
import streamlit as st
from .planner import RepoSignals
from .security_utils import sanitize_text

def _blurb_readme(sig: RepoSignals) -> str:
    if not sig.readme_path:
        return "No README found. This repo would benefit from a brief purpose and quickstart."
    return "The README anchors purpose and setup. Start here to understand goals, usage, and any demo instructions."

def _blurb_deps(sig: RepoSignals) -> str:
    pipn = len(sig.deps.get("pip", []))
    if pipn == 0:
        return "No Python dependencies detected. Running locally should be straightforward."
    return f"Dependencies shape runtime and reproducibility. This repo lists {pipn} Python package(s) in requirements."

def _blurb_entry(sig: RepoSignals) -> str:
    if not sig.entrypoint:
        return "No clear app entrypoint detected. Consider documenting how to run the project."
    return "The entrypoint is the quickest path to a live demo. Use it to validate install and wiring."

def render_tour(sig: RepoSignals) -> None:
    """Render a simple 3-stop repository tour.

    Persists current index in session_state['tour_ix'] and resets when the
    underlying repo root changes (tracked via session_state['tour_repo_root']).
    Content comes from internal heuristics (no user input) but we still pass
    through sanitize_text defensively for UI safety & parity.
    """
    cur_root = getattr(sig, "repo_root", "")
    if st.session_state.get("tour_repo_root") != cur_root:
        st.session_state["tour_repo_root"] = cur_root
        st.session_state["tour_ix"] = 0

    stops = [
        ("README", _blurb_readme(sig), sig.readme_path or "(missing)"),
        ("Dependencies", _blurb_deps(sig), "requirements.txt"),
        ("Entrypoint", _blurb_entry(sig), sig.entrypoint or "(undocumented)"),
    ]
    ix = int(st.session_state.get("tour_ix", 0))
    ix = max(0, min(ix, len(stops)-1))
    title, blurb, ref = stops[ix]

    st.subheader("Repo Tour")
    st.caption(f"Stop {ix+1}/{len(stops)} — {title}")
    st.write(sanitize_text(blurb))
    st.caption(f"Reference: `{sanitize_text(ref)}`")

    c1, c2 = st.columns(2)
    if c1.button("Prev", disabled=ix == 0):
        st.session_state["tour_ix"] = max(ix - 1, 0)
    if c2.button("Next", disabled=ix == len(stops) - 1):
        st.session_state["tour_ix"] = min(ix + 1, len(stops) - 1)
