# --- bootstrap import path so app can see modules in repo root and ./src ---
import sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
for p in (ROOT, SRC):
    p_str = str(p)
    if p_str not in sys.path:
        sys.path.insert(0, p_str)
# ---------------------------------------------------------------------------

# streamlit_app.py — flat imports, no relative/package deps
import os
import streamlit as st

# MVP modules (all at repo root in your Space)
from planner import extract_repo_signals, plan_walkthrough
from coach import render_coach_page
from tour import render_tour

st.set_page_config(page_title="GitHub GuideBot — MVP v1", layout="wide")
st.title("GitHub GuideBot — MVP v1")
st.caption(f"DEMO_MODE={os.getenv('DEMO_MODE','0')}  •  Running in Docker")

with st.sidebar:
    st.header("Demo Controls")
    repo_root = st.text_input("Repo root", value=".")
    trigger = st.button("Generate Walkthrough")

# Generate signals/plan once, then render Coach + Tour
if trigger or "last_signals" in st.session_state:
    if trigger:
        sig = extract_repo_signals(repo_root)
        st.session_state["last_signals"] = sig
        st.session_state["last_plan"] = plan_walkthrough(sig)

    sig = st.session_state["last_signals"]
    render_coach_page(repo_root)
    render_tour(sig)
else:
    st.write("Use the sidebar to generate the walkthrough.")
