# Quality Assurance Snapshot

The sample fixtures bundled in `examples/` are used to validate retrieval quality during publication review.

## Precision@K (sample corpus)

| Query | Expected source | k | Hits within k |
|-------|-----------------|---|---------------|
| "What does this sample project expose?" | `sample_repo/README.md` | 3 | ✅ (README.md appears twice, app.py once) |
| "What is an API status code?" | `uploaded:understanding_apis_excerpt.txt` | 2 | ✅ (both results reference the uploaded excerpt) |

Running `python examples/run_sample.py` prints the raw retrieval output for auditors.

## Test Suite

| Command | Purpose |
|---------|---------|
| `pytest` | full unit/integration suite (62 tests) |
| `python examples/run_sample.py` | deterministic retrieval smoke test |

All results above were generated on 2025-09-30 using Python 3.13.5 on Windows.
