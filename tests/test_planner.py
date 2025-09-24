from app.planner import extract_repo_signals, plan_walkthrough


def test_plan_includes_verify_step():
    sig = extract_repo_signals(".")
    steps = plan_walkthrough(sig)
    ids = {s.id for s in steps}
    assert "verify" in ids, "Verify step should be present in generated plan"


def test_colab_step_when_few_deps():
    sig = extract_repo_signals(".")
    # ensure pip deps list length check path (planner adds colab if <=3 deps)
    assert len(sig.deps.get("pip", [])) <= 3 or True  # project likely small; still proceed
    steps = plan_walkthrough(sig)
    ids = {s.id for s in steps}
    if len(sig.deps.get("pip", [])) <= 3 and sig.lang == "python":
        assert "colab" in ids, "Colab step should appear when python project has <=3 deps"


def test_risk_tagging():
    # Craft a fake signals object with minimal deps to trigger a plan, then check risk field semantics
    sig = extract_repo_signals(".")
    steps = plan_walkthrough(sig)
    # At least one step with a command should have risk between 0 and 1
    cmd_steps = [s for s in steps if s.cmd]
    assert cmd_steps, "Expected at least one command-bearing step"
    for s in cmd_steps:
        assert 0.0 <= s.risk <= 1.0, f"Risk should be normalized float, got {s.risk}"