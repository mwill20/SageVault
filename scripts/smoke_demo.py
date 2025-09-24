"""Minimal deterministic smoke test for demo / Spaces build.

Usage:
  python scripts/smoke_demo.py

It imports the planner against the current repository root ("."), generates
steps, asserts that a final 'verify' step exists and is last, then prints
SMOKE_OK for CI / Hugging Face build logs.
"""
import sys, os

# Ensure project root (parent of scripts/) is on sys.path for 'app' package import
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
  sys.path.insert(0, ROOT)

from app.planner import extract_repo_signals, plan_walkthrough


def main() -> int:
    sig = extract_repo_signals(".")
    steps = plan_walkthrough(sig)
    ids = [s.id for s in steps]
    assert "verify" in ids, "verify step missing"
    assert ids[-1] == "verify", "verify step not last"
    # basic invariants: no duplicate ids
    assert len(ids) == len(set(ids)), "duplicate step ids detected"
    print("SMOKE_OK", len(steps))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
