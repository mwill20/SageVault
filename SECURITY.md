# Security

## Scope
Public repositories only. User-supplied LLM API keys are held in session memory only (never logged, persisted, or transmitted elsewhere). No private repo cloning, credential harvesting, or command execution is performed.

## Defenses
- **Sanitization & Redaction**: `sanitize_text` strips control chars; `redact_secrets` masks tokens (GitHub PAT, OpenAI-style keys, AWS keys, JWT fragments, Google API keys) before display/storage.
- **Injection Heuristics**: `INJECTION_PATTERNS`, `injection_score()` flag prompt injection attempts; `penalize_suspicious()` down-weights and may filter suspicious chunks.
- **Retrieval Diversity Guard**: `penalize_suspicious()` also caps per-file dominance (prevents a single file monopolizing context, mitigating targeted poisoning).
- **Dangerous Command Warnings**: `label_dangerous_commands` / `warn_dangerous` annotate high‑risk operations (git push --force, rm -rf, curl | bash, chmod 777) with a WARN preface and safer guidance.
- **Provenance Transparency**: Each cited chunk carries file path, chunk index, and similarity score; links generated for traceability back to source on GitHub.
- **Hierarchical Memory Hygiene**: Context assembly prefers: (1) fresh retrieval (episodic), then (2) recent window, (3) decisions ledger (compact facts), (4) optional summary digest—bounded by token/char budgets.
- **No Execution**: The application never executes user-supplied commands—LLM output is instructional only.

## Data Handling
- No long-term storage of user queries or answers beyond the live Streamlit session state.
- In-memory vector index is ephemeral (recreated per session / hash invalidation). No embeddings are exfiltrated.

## Limitations / Non-Goals
- No advanced sandboxing (e.g., static taint analysis) of repository code.
- Token counting currently heuristic; high-fidelity model-specific tokenization may be added later.
- Injection scoring is regex-based (heuristic) and may produce false negatives/positives.

## Reporting Vulnerabilities
Please open a GitHub issue with a clear reproduction. Do not include real secrets—use placeholders. For sensitive findings you prefer to disclose privately, state so in the issue and request a contact channel.

## Future Hardening (Planned)
- Model-specific token accounting and budget-driven context trimming.
- Extended secret detectors (custom patterns, entropy heuristics).
- Retrieval injection penalty metrics surfaced in a developer diagnostics panel.
- Red-team test harness: synthetic repos containing staged injections, secret leaks, and large-file spam.

---
Security posture: prioritize determinism (code-enforced guards) over overlong prompts; keep runtime prompt lean so real repository context dominates.
