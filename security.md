# Secu## Enhanced Security Controls

### 🛡️ **File Type Security**
- **Safe File Filtering**: Comprehensive allowlist of text/code files (.py, .js, .md, .json, .ipynb, etc.)
- **Binary File Blocking**: Automatically blocks executables (.exe, .bat, .ps1), archives (.zip, .tar), and media files
- **Size Limits**: Files exceeding 100KB are truncated to prevent resource exhaustion
- **Extension Validation**: Files without extensions are checked against known safe patterns (README, LICENSE, etc.)

### 🔐 **Content Security**
- **Sanitization & Redaction**: Control characters stripped, Markdown links neutralized, secrets (API keys, JWTs, tokens) replaced with `[REDACTED]`
- **LLM Safety Instructions**: System explicitly prevents code execution - only reads and reproduces content
- **Prompt Injection Heuristics**: Regex-based scoring for suspicious patterns ("ignore previous instructions", "reveal system prompt")
- **Input Validation**: Multi-layer content filtering before processing

### 🎯 **Retrieval Security**
- **README Prioritization**: Ensures documentation context is always available for better understanding
- **Diversity Guard**: Retrieval results capped per file path to prevent single-file dominance
- **Similarity Thresholds**: Low-relevance content filtered out to prevent information leakage
- **Provenance Tracking**: All snippets include file path, chunk ID, and similarity scores

### ⚠️ **Security Override (Advanced Users)**
For security professionals and advanced users who need to analyze potentially risky content:
- **Risk Assessment**: System identifies and warns about potentially malicious files/repositories
- **Informed Consent**: Clear warnings about risks with explicit user confirmation required
- **Audit Trail**: All override decisions logged for accountability
- **Controlled Access**: Override available only when user explicitly accepts responsibility

### 🔍 **Session Security**
- **Memory-Only Storage**: API keys and tokens never written to disk or logs
- **Session Isolation**: Each session maintains separate context and credentials
- **Automatic Cleanup**: Sensitive data cleared when session ends
- **No Persistent Storage**: Vector databases and processed content cleared between sessionsSupported Scope
- This project only supports **public GitHub repositories**.
- LLM API keys are kept **in-session only** and never written to disk or logs.

## Security Controls
- **Sanitization & Redaction**  
  Control characters are stripped, Markdown links neutralized, and secrets (API keys, JWTs, tokens) are replaced with `[REDACTED]`.

- **Prompt Injection Heuristics**  
  Inputs are scored with regex-based patterns (e.g., “ignore previous instructions,” “reveal system prompt”). Suspicious chunks are down-ranked or flagged.

- **Diversity Guard**  
  Retrieval results are capped per file path to prevent one file from dominating answers.

- **Dangerous Command Detection**  
  High-risk commands (`rm -rf`, `git push --force`, `curl | bash`, `chmod 777`) are labeled with WARN banners before display.

- **Provenance**  
  All answer snippets carry file path, line numbers, and similarity score so users can verify.

- **Memory Hygiene**  
  Context is assembled hierarchically (episodic → rolling window → ledger → summaries). Ledger entries are capped to prevent unbounded growth.

## Reporting Vulnerabilities
Please open a GitHub issue with clear reproduction steps. Do **not** include sensitive keys or private data.  
Coordinated disclosure is appreciated.

## Planner Hardening
All planner steps are scored by `penalize_suspicious()` and surfaced via `warn()`.  
Heuristics flag dangerous shells (e.g., `curl … | sh`, `rm -rf`). Commands may be **blocked** or **downgraded**.  
**Caveat:** Heuristics are best-effort; users must review commands before execution. No secrets are logged; API keys stay in session memory only.

### Coach Mode & Repo Tour
Coach Mode and the Repo Tour produce **suggested** steps and orientation blurbs derived from static repository files (README, dependency manifests, entrypoints). They:
- Never execute commands automatically.
- Sanitize and redact content before display.
- Surface suspicious patterns instead of hiding them.

Users are responsible for validating commands, especially in production or privileged shells. Treat suggestions as starting points, not guaranteed-safe prescriptions.

## Global Safety Gate
All steps and free-form text pass through a unified security gate: `penalize_suspicious` + `redact_secrets` with surfaced warnings via `warn()`. Commands are never executed by the application; any high‑risk shell pipelines (e.g., `curl … | sh`) may be blocked or replaced before display.
