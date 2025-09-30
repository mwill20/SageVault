# Contributing to SageVault

Thanks for your interest in improving SageVault! We welcome pull requests that enhance the RAG workflow, documentation, or tooling.

## Getting Started

1. **Fork and clone** the repository, then create an isolated environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. **Run the sample data smoke test** to confirm your environment:
   ```bash
   python examples/run_sample.py
   ```
3. **Run the test suite** before opening a PR:
   ```bash
   pytest
   ```

## Workflow

- Create a topic branch from `main` (e.g. `feat/langchain-toggle`).
- Keep commits focused; include tests and documentation when behaviour changes.
- Run `pytest` and the Streamlit app (`streamlit run streamlit_app_clean.py`) to verify everything still works.
- Submit a PR referencing any relevant issues and describe manual test steps.

## Reporting Issues

Use [GitHub Issues](https://github.com/mwill20/SageVault/issues) for bug reports or feature ideas. Include reproduction steps, expected behaviour, and environment details.

Thanks for helping make SageVault better!
