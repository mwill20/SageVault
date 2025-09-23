import importlib

from app.planner import extract_repo_signals


def test_streamlit_app_imports():
    # Should import without executing blocking code (Streamlit safe at import time)
    mod = importlib.import_module("app.streamlit_app")
    assert mod is not None


def test_extract_repo_signals_fields():
    sig = extract_repo_signals(".")
    assert hasattr(sig, "readme_path")
    assert hasattr(sig, "deps") and isinstance(sig.deps, dict)
    assert hasattr(sig, "entrypoint")
    assert hasattr(sig, "lang")