# tests/conftest.py
from __future__ import annotations
import json, csv, os, sys
from typing import Any, Dict, List
import pytest

# Ensure the repository root (which contains the 'app' package) is on sys.path
# even if pytest is invoked from a parent directory.
_THIS_DIR = os.path.dirname(__file__)
_REPO_ROOT = os.path.abspath(os.path.join(_THIS_DIR, os.pardir))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

def pytest_addoption(parser):
    parser.addoption(
        "--audit-report-dir",
        action="store",
        default="artifacts",
        help="Directory to write test audit reports (JSON/CSV/MD).",
    )

@pytest.fixture
def audit(request):
    """
    Log a human-friendly audit row for this test.

    Example:
        audit(kind="prompt injection",
              query="Please ignore previous instructions",
              result="penalized")
    """
    node = request.node
    if not hasattr(node, "_audit_logs"):
        node._audit_logs = []
    def _log(kind: str, query: str = "", result: str = ""):
        node._audit_logs.append({"kind": kind, "query": query, "result": result})
    return _log

def _kind_from_nodeid(nodeid: str) -> str:
    n = nodeid.lower()
    if "injection" in n: return "prompt injection"
    if "memory" in n:    return "memory"
    if "security" in n:  return "security"
    return "general"

def _desc_from_item(item) -> str:
    # Use test function docstring if present to explain intent
    func = getattr(item, "function", None)
    doc = (func.__doc__ or "").strip() if func else ""
    return " ".join(doc.split())[:140] if doc else ""

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    if rep.when != "call":
        return
    config = item.config
    if not hasattr(config, "_audit_results"):
        config._audit_results = []

    logs = getattr(item, "_audit_logs", []) or []
    desc = _desc_from_item(item)
    if not logs:
        logs = [{"kind": _kind_from_nodeid(item.nodeid), "query": "", "result": ""}]

    for e in logs:
        config._audit_results.append({
            "test": item.nodeid,
            "description": desc,
            "kind": e.get("kind",""),
            "query": e.get("query",""),
            "result": e.get("result",""),
            "outcome": "pass" if rep.passed else ("fail" if rep.failed else rep.outcome),
            "duration_s": getattr(rep, "duration", 0.0),
        })

def _to_markdown(rows: List[Dict[str, Any]]) -> str:
    headers = ["Type of test", "Attempted query", "Result", "Pass/Fail", "Description", "Test", "Duration (s)"]
    md = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"]*len(headers)) + "|"]
    for r in rows:
        md.append("| " + " | ".join([
            r.get("kind",""),
            (r.get("query","") or "").replace("\n"," ")[:90],
            r.get("result",""),
            r.get("outcome",""),
            (r.get("description","") or "").replace("\n"," ")[:90],
            r.get("test",""),
            f'{r.get("duration_s",0.0):.2f}',
        ]) + " |")
    return "\n".join(md)

def pytest_terminal_summary(terminalreporter, exitstatus):
    config = terminalreporter.config
    rows = getattr(config, "_audit_results", [])
    report_dir = config.getoption("--audit-report-dir")
    os.makedirs(report_dir, exist_ok=True)

    terminalreporter.section("Audit Summary (type, query, result, pass/fail)")
    if not rows:
        terminalreporter.write_line("No audit data collected.")
        return

    # Wider table with description so you can SEE what's being tested
    colw = {"kind":18, "query":42, "result":12, "outcome":8, "desc":40}
    def clip(s, w):
        s = (s or "").replace("\n"," ")
        return (s[:w-1] + "…") if len(s) > w else s
    header = (
        f"{'Type of test':{colw['kind']}}  "
        f"{'Attempted query':{colw['query']}}  "
        f"{'Result':{colw['result']}}  "
        f"{'Pass/Fail':{colw['outcome']}}  "
        f"{'Description':{colw['desc']}}"
    )
    terminalreporter.write_line(header)
    terminalreporter.write_line("-"*len(header))
    for r in rows:
        terminalreporter.write_line(
            f"{clip(r['kind'],colw['kind']):{colw['kind']}}  "
            f"{clip(r['query'],colw['query']):{colw['query']}}  "
            f"{clip(r['result'],colw['result']):{colw['result']}}  "
            f"{clip(r['outcome'],colw['outcome']):{colw['outcome']}}  "
            f"{clip(r.get('description',''),colw['desc']):{colw['desc']}}"
        )

    # Persist reports
    json_path = os.path.join(report_dir, "test_audit_report.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2)

    csv_path = os.path.join(report_dir, "test_audit_report.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=[
            "test","description","kind","query","result","outcome","duration_s"
        ])
        w.writeheader()
        w.writerows(rows)

    md_path = os.path.join(report_dir, "test_audit_report.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(_to_markdown(rows))

    terminalreporter.write_line(f"\nReports → {json_path}, {csv_path}, {md_path}")
