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