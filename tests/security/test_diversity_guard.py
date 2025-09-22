import pytest

try:
    from app.security_utils import diversity_guard
except ImportError:
    from security_utils import diversity_guard

def test_diversity_guard_limits_duplicates():
    items = [{"path": "a.py"}, {"path": "a.py"}, {"path": "b.py"}, {"path": "a.py"}]
    out = diversity_guard(items, key="path", max_per_key=2)
    assert sum(1 for it in out if it["path"] == "a.py") <= 2
