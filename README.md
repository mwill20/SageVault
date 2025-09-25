# GitHub GuideBot

"Learn GitHub by doing" — e## 🚀 Quick Start

```powershell
# Clone and setup
git clone https://github.com/mwill20/github-guidebot.git
cd github-guidebot
python -m venv .venv
.\.venv\Scripts\activate  # Windows
# or source .venv/bin/activate  # macOS/Linux
pip install -r requirements_clean.txt

# Run the enhanced app
streamlit run streamlit_app_clean.py
```

## 📖 Usage

### **Analyze GitHub Repositories**
1. Paste a public GitHub URL (e.g., `https://github.com/user/repo`)
2. Optionally add your GitHub Personal Access Token for higher rate limits
3. Configure chunk size and overlap using the sidebar sliders
4. Click "🔍 Analyze Repository" 
5. Ask questions and get answers with file citations and similarity scores

### **Upload Documents**
1. Use the "📄 Upload Documents" section in the sidebar
2. Select multiple files (PDF, DOCX, code files, etc.)
3. Click "🔍 Index Documents"
4. Ask questions about your uploaded content

### **Multi-Source Analysis**
- Index both a GitHub repository AND upload documents in the same session
- Ask questions that span both sources
- Get unified results with clear source attribution

### **Configuration Options**
- **Chunk Size**: 200-1500 characters (default: 500)
- **Overlap**: 0-50% (default: 10%)
- **GitHub Token**: Optional for increased API limits
- **LLM Provider**: Groq or OpenAI with your API keynd, and reproduce repos step-by-step with an LLM tutor.

---

## 🚀 Enhanced RAG System (Current Version)

This advanced app provides **Retrieval-Augmented Generation** over public GitHub repositories **AND** uploaded documents with comprehensive safety rails, configurable chunking, and multi-source indexing.

### ✨ **New Features**
- **📄 Document Upload**: Support for PDF, DOCX, TXT, MD, Python, JavaScript, JSON, YAML and more
- **🔧 Configurable Chunking**: Adjustable chunk size (200-1500 chars) and overlap (0-50%)
- **🎯 README Prioritization**: Always includes README content in search results for better context
- **🔗 Multi-Source Sessions**: Index both GitHub repos AND uploaded documents simultaneously
- **🛡️ Enhanced Security**: Expanded file type filtering with Jupyter notebook (.ipynb) support
- **🔑 GitHub Token Support**: Optional Personal Access Token for higher API limits
- **⚡ Improved Performance**: Optimized vector search with semantic similarity ranking

### 📁 **Supported File Types**
- **Code**: .py .js .ts .jsx .tsx .java .cpp .c .h .hpp .cs .php .rb .go .rs .swift .kt .scala .ipynb
- **Web**: .html .htm .css .scss .sass .less
- **Config**: .json .yml .yaml .xml .toml .cfg .ini .conf .config .env
- **Documentation**: .md .txt .rst .adoc .wiki
- **Scripts**: .sh .bash .zsh .sql .dockerfile
- **Documents**: PDF, DOCX (via upload)
- **Special**: README, LICENSE, CHANGELOG, CONTRIBUTING, MAKEFILE (without extensions)

### 🔒 **Security Features**
- **File Type Filtering**: Blocks binary files, executables, and potentially malicious content
- **LLM Safety Instructions**: Prevents code execution - system only reads and reproduces content
- **Size Limits**: Files > 100KB are truncated for safety
- **Input Sanitization**: Heuristic injection detection and content redaction
- **Session-Only Storage**: API keys and tokens stored only in memoryBot

“Learn GitHub by doing” — explore, understand, and reproduce repos step-by-step with an LLM tutor.

---

## RAG MVP (current default)

This simplified app focuses on Retrieval-Augmented Generation over public GitHub repositories with built‑in safety rails and a lightweight memory ledger.

- Allowlist: .md .py .txt .rst .cfg .ini .toml .yaml .yml .js .ts
- Size cap: files > 80 KB are skipped
- Provenance: each answer shows file links and similarity scores
- Keys: entered in the UI, used only in-session (not logged)

Run locally:

```powershell
python -m venv .venv; .\.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app/streamlit_app.py
```

Usage:
- Paste a public GitHub URL and click “Analyze repo & build index”.
- Ask a question. If you provide an API key for Groq or OpenAI, the app calls the model with secure context; otherwise it returns an extractive fallback from top chunks.

Safety notes:
- Input/Output goes through heuristic checks and redaction.
- Only safe text files are fetched (allowlist + size cap).
- No shell commands are executed by the app.

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
