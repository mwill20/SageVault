---
title: GitHub GuideBot
emoji: 🎯
colorFrom: indigo
colorTo: gray
sdk: streamlit
app_file: app/streamlit_app.py
pinned: false
license: mit
short_description: Learn GitHub by doing – explore repos with a secure guided AI tutor.
---

# GitHub GuideBot

“Learn GitHub by doing” — explore, understand, and reproduce repos step-by-step with an LLM tutor.

---

## Features
- **Repo Summarization** — beginner- or expert-level overviews.
- **Interactive Q&A** — ask natural language questions about repo files.
- **Reproduction Helpers** — Colab button for newcomers, VSCode setup guides for advanced users.
- **Build-Your-Own Mode** — scaffold a new repo with README, CONTRIBUTING, SECURITY docs.

---

## Getting Started

### Prerequisites
- Python 3.10–3.12
- A valid LLM API key (OpenAI, Anthropic, Gemini, Groq, etc.)

### Installation
```bash
git clone https://github.com/mwill20/github-guidebot.git
cd github-guidebot
python -m venv .venv
.\.venv\Scripts\activate  # Windows
# or source .venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
Run
bash
Copy code
streamlit run app/streamlit_app.py
Paste a public GitHub repo URL and your API key in the UI to start exploring.

Security Model
Session-only keys — your LLM key lives in memory for the session only.

Injection heuristics — malicious prompt attempts are flagged and down-ranked.

Diversity guard — retrieval caps duplicates to avoid echoing one file.

Dangerous commands — risky commands are surfaced with WARN callouts.

Provenance — file path, line numbers, and similarity score are shown with each answer.

Redaction — secrets and tokens are stripped before being sent to the model.

Memory Routing
GuideBot uses a layered memory strategy:

Episodic memory — captures recent exchanges.

Rolling window — maintains current context window.

Decisions ledger — persistent log of key actions/answers.

Summaries — compress older history to stay under token limits.

This ensures transparency, prevents overflow, and keeps responses grounded in prior decisions.

Development
Run Tests
bash
Copy code
pytest -q --audit-report-dir artifacts
You’ll see a terminal summary like:

markdown
Copy code
Type of test        Attempted query                  Result     Pass/Fail  Description
--------------------------------------------------------------------------------------
prompt injection    Ignore previous instructions.    flagged    pass       Flags obvious prompt-injection phrases …
Full reports are saved to:

artifacts/test_audit_report.json

artifacts/test_audit_report.csv

artifacts/test_audit_report.md

Continuous Integration
Tests run automatically on push/PR via GitHub Actions (.github/workflows/ci.yml).
Audit reports are uploaded as downloadable artifacts.

Contributing
Pull requests are welcome. Please ensure all tests pass and that any new features include audit logs.

License
MIT

## Coach Mode (Guided Walkthrough)

Coach Mode generates a structured, citation-backed onboarding plan for a **local clone** of a repository. It never executes commands – it only surfaces them with provenance so you can copy/paste intentionally.

Highlights:
- Step list with: Title • Why it matters • (Optional) command • Citations (e.g. `README`, `requirements.txt`)
- Risk & injection indicators: suspicious command patterns (curl|bash piping, destructive ops) are flagged with a ⚠️ badge.
- Optional Colab bootstrap step when the repo looks like Python and has a small dependency surface (≤3 packages).
- Verify step always appended – prompts you to run tests / smoke the app before moving on.

Safety Posture:
- No shell execution or file writes are performed automatically.
- Commands are derived heuristically from repo signals (README text, dependency files, entrypoint scripts) and sanitized.
- Potentially dangerous substrings (e.g. `rm -rf`, `:(){:|:&};:`) are surfaced instead of hidden.
- All commands displayed are safety-scored and may be redacted or blocked by the global security gate.

Usage:
1. Open the sidebar → Coach Mode section.
2. Provide local repo root path (where you cloned the repo).
3. Click Generate Walkthrough.
4. Review each step, copy commands manually, run locally, then proceed to Verify.
5. Re‑generate after pulling upstream changes to refresh signals.

## Planner & Tour Safety Notes

The walkthrough planner and repo tour are **heuristic explainers** – they infer intent from static files. They may miss custom setup scripts or edge cases. Always review generated commands before running, especially in privileged environments. The system does not fetch or execute arbitrary network content beyond the public GitHub files you load.

## Repo Tour
A lightweight, three-stop orientation component rendered after generating a walkthrough:
- Stop 1: README — purpose & high-level intent
- Stop 2: Dependencies — what runtimes or packages you need
- Stop 3: Entrypoint — how to actually run / launch the project

Navigation uses Prev/Next buttons with session-based index (`tour_ix`). The index resets automatically when you change the repo root. All blurbs are sanitized and never execute code.

## Follow-up Ideas
- Inline warning badges directly below blocked / redacted commands.
- Configurable policy mode (warn-only vs block dangerous pipelines).
- Additional secret patterns (HuggingFace, Slack, GitLab tokens, JWT heuristics).
- Lightweight AST-based command parser to reduce false positives.
- Optional per-step justification LLM call with strict system prompt.
- Cumulative risk scoring summary sidebar card.

### Coach Mode
Generates a step-by-step walkthrough for this repo with **copyable commands**, **citation chips** (e.g., `README`, `requirements.txt`), and **safety warnings** for risky patterns.  
**How to use:** Enter repo root → **Generate Walkthrough** → follow numbered steps → run **Verify**. Optional **Colab** appears when Python deps are small (≤3). Planner output is passed through the security layer and redacted when needed.

## Deploy

Local run (development):
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .\.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app/streamlit_app.py
```

Deterministic demo mode:
```bash
DEMO_MODE=1 streamlit run app/streamlit_app.py
```
Locks the repo input to this project so retrieval & answers are stable.

Hugging Face Spaces:
- The YAML front matter (top of this README) configures the Space.
- Optionally set a Space secret for any LLM API key; without one the app falls back to semantic-only answers.

Smoke check (used for CI/Spaces build logs):
```bash
python scripts/smoke_demo.py
# Outputs: SMOKE_OK <nsteps>
```
This validates the planner returns a final `verify` step.
