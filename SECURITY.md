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
