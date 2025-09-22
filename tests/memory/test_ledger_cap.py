import pytest

try:
    from app.memory_orchestrator import update_ledger
except ImportError:
    from memory_orchestrator import update_ledger

def test_update_ledger_caps_length():
    state = {"ledger": []}
    for i in range(200):
        state = update_ledger(state, {"role": "user", "content": f"item {i}"}, cap=50)
    assert len(state["ledger"]) <= 50
    # newest entries should be present
    assert any("item 199" in (e.get("content","")) for e in state["ledger"])
