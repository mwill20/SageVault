# Changelog

All notable changes to this project will be documented here. This project follows a simple Phase-based log (earliest at top). Use semantic commit messages for future entries if possible.

## Phase 1 (Initial RAG + UI Foundation)
### Added
- Basic Streamlit interface: repo URL input, audience selector, Analyze & Q&A buttons.
- GitHub fetch: tree retrieval, file allowlist, prioritization (README, license, setup files).
- Simple keyword-based Q&A (frequency scoring + README bonus).
- Corpus slice & in-memory storage for basic exploration.
- Session state for corpus persistence across reruns.

### Changed
- N/A (initial scaffold).

### Fixed
- Basic validation of GitHub URL pattern.

### Notes
- No LLM integration; purely heuristic semantic-less approach.

## Phase 2 (LLM + Semantic Indexing & Controls)
### Added
- LLM provider selection (Gemini, Groq, OpenAI, Claude, XAI, OpenRouter, none).
- Secure API key handling (session only, never logged).
- Semantic embeddings via `sentence-transformers` + Chroma in-memory collection.
- Adjustable chunk parameters (size & overlap) with guidance and sidebar UI.
- Corpus hashing to skip redundant embedding builds.
- Multi-provider abstraction via `llm_utils.call_llm` with provider-specific adapters.
- Fallback reasoning text when LLM not used (no provider, missing key, provider error).
- Repo metadata + default branch persisted for citation link generation.
- Error handling for GitHub rate limits and network issues.
- NumPy version pin (<2.0) to mitigate removed alias incompatibilities.
- Sidebar refactor consolidating LLM + indexing configuration.
- Multi-chunk semantic synthesis fallback (stitches top-N chunks when no LLM answer returned).

### Changed
- Refactored layout from dual column to main + sidebar.
- Chunking strategy (500 default, adjustable 300–1200, overlap percent).
- Index build now cached by (files, lengths, chunk params) hash.
- Answer generation pipeline now capable of semantic + (future) LLM synthesis.

### Fixed
- Potential `NameError` on `hits` when rendering before user asks a question.
- Indentation errors during layout refactor.
- Safe handling when no indexable files are found.

### Notes
- Embedding build still synchronous; future optimization: parallel raw fetch & caching.
- Token accounting & rate limit guard not yet implemented.
- Multi-chunk semantic synthesis in fallback planned next.

## Upcoming (Planned)
- Multi-chunk semantic synthesis (combine top-N snippets before LLM prompt & fallback) [IN PROGRESS].
- Token estimate & truncation logic for context safety.
- Optional parallel file fetch with caching.
- Manual rebuild/reset button for index.

---
Guideline: For future phases, add sections using the same headings (Added / Changed / Fixed / Notes). Keep entries terse but specific.
