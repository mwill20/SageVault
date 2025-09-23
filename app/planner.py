from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict

@dataclass
class RepoSignals:
    repo_root: str
    readme_path: str | None
    deps: Dict[str, list]          # {"pip": ["streamlit","chroma"], "node": []}
    entrypoint: str | None
    lang: str | None
    notes: list[str]

@dataclass
class PlanStep:
    id: str
    title: str
    why: str
    cite: list[str]
    cmd: str | None = None
    risk: float = 0.0  # 0..1

def extract_repo_signals(repo_root: str) -> RepoSignals:
    root = Path(repo_root)
    readme = next((str(p) for p in [root/"README.md", root/"Readme.md"] if p.exists()), None)
    entry = str(root/"app/streamlit_app.py") if (root/"app/streamlit_app.py").exists() else None
    pip_deps = []
    req = root/"requirements.txt"
    if req.exists():
        try:
            raw_req = req.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            raw_req = req.read_text(encoding="utf-8", errors="ignore")
        pip_deps = [l.strip().split("==")[0] for l in raw_req.splitlines() if l.strip() and not l.startswith("#")]
    lang = "python" if pip_deps or (entry and entry.endswith(".py")) else None
    return RepoSignals(str(root), readme, {"pip": pip_deps, "node": []}, entry, lang, notes=[])

def _simple_risk(cmd: str | None) -> float:
    if not cmd: return 0.0
    bad = ["curl", "| sh", "rm -rf", "mkfs", ":(){", "Invoke-WebRequest -UseBasicParsing"]
    return 0.8 if any(b in cmd for b in bad) else 0.05

def plan_walkthrough(sig: RepoSignals) -> List[PlanStep]:
    steps: List[PlanStep] = []
    steps.append(PlanStep("clone", "Clone repo", "Get the code locally.", ["README"], 
                          "git clone https://github.com/your-org/github-guidebot && cd github-guidebot"))
    if sig.deps.get("pip"):
        steps.append(PlanStep("deps", "Install dependencies", "Prepare environment.", ["requirements.txt"], 
                              "pip install -r requirements.txt"))
    if sig.entrypoint:
        steps.append(PlanStep("run", "Run the app", "Verify it boots.", ["app/streamlit_app.py"],
                              "streamlit run app/streamlit_app.py"))
    # Optional Colab if simple deps
    if sig.lang == "python" and len(sig.deps.get("pip", [])) <= 3:
        steps.append(PlanStep("colab", "Open in Colab (optional)", "Reproduce in the cloud.", ["README"], 
                              "https://colab.research.google.com/#create=true"))

    steps.append(PlanStep("verify", "Verify", "Check the app renders and shows Signals + Tour.", ["README"]))
    # Tag risk
    for s in steps: s.risk = _simple_risk(s.cmd)
    return steps
