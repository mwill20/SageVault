# Security Policy

## Supported Scope
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
