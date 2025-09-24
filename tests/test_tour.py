from app.planner import RepoSignals
from app.tour import _blurb_readme, _blurb_deps, _blurb_entry, render_tour

def test_blurbs_non_empty():
    sig = RepoSignals(".", "README.md", {"pip": ["streamlit"]}, "app/streamlit_app.py", "python", [])
    assert _blurb_readme(sig)
    assert _blurb_deps(sig)
    assert _blurb_entry(sig)

def test_blurbs_handle_missing():
    sig = RepoSignals(".", None, {"pip": []}, None, None, [])
    assert "No README" in _blurb_readme(sig)
    assert "No Python dependencies" in _blurb_deps(sig)
    assert "No clear app entrypoint" in _blurb_entry(sig)


def test_dependency_count_blurb_mentions_number():
    """When deps exist, the blurb should mention the count."""
    sig = RepoSignals(".", "README.md", {"pip": ["a", "b", "c"]}, "app/streamlit_app.py", "python", [])
    blurb = _blurb_deps(sig)
    assert "3 Python package" in blurb


def test_render_tour_resets_index_on_repo_change(monkeypatch):
    """render_tour should reset tour_ix when repo_root changes."""
    import app.tour as tour_mod

    class StubST:
        session_state = {}
        def subheader(self, *_, **__): pass
        def caption(self, *_, **__): pass
        def write(self, *_, **__): pass
        def columns(self, _sizes):
            class Col:
                def button(self, *_, **__):
                    return False  # never advance automatically
            return [Col(), Col()]
    # Swap streamlit reference inside module
    orig_st = tour_mod.st
    tour_mod.st = StubST()
    try:
        sig1 = RepoSignals("/tmp/repoA", "README.md", {"pip": []}, None, "python", [])
        render_tour(sig1)
        assert tour_mod.st.session_state.get("tour_ix") == 0
        # Pretend user advanced (manually set index)
        tour_mod.st.session_state["tour_ix"] = 2
        sig2 = RepoSignals("/different/repoB", "README.md", {"pip": []}, None, "python", [])
        render_tour(sig2)  # new root should trigger reset
        assert tour_mod.st.session_state.get("tour_ix") == 0, "tour_ix should reset when repo root changes"
    finally:
        tour_mod.st = orig_st


def test_render_tour_clamps_out_of_range_index(monkeypatch):
    """If tour_ix is manually set beyond bounds, render_tour should clamp it inside valid range."""
    import app.tour as tour_mod

    class StubST:
        session_state = {"tour_ix": 999}  # deliberately huge
        def subheader(self, *_, **__): pass
        def caption(self, *_, **__): pass
        def write(self, *_, **__): pass
        def columns(self, _sizes):
            class Col:
                def button(self, *_, **__):
                    return False
            return [Col(), Col()]
    orig_st = tour_mod.st
    tour_mod.st = StubST()
    try:
        sig = RepoSignals("/clamp/repo", "README.md", {"pip": []}, None, "python", [])
        render_tour(sig)
        # There are exactly 3 stops; max valid index internally is 2; after clamp tour_ix should be <=2
        assert tour_mod.st.session_state.get("tour_ix") <= 2
    finally:
        tour_mod.st = orig_st
