# SageVault

![SageVault Logo](assets/sagevault-logo.png)
![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)

**SageVault** is a security‑minded **RAG (Retrieval‑Augmented Generation)** app for exploring a **single source per session**: either a public **GitHub repo** or a set of **uploaded documents**. It indexes content, retrieves relevant chunks, and answers questions with citations. Runs locally with Streamlit and supports multiple LLM providers.

- **Retrieval:** Chroma vector store (configurable chunk size/overlap)
- **LLMs:** OpenAI, Anthropic, Google Gemini, Groq (keys kept **in‑session only**)
- **Safety:** Allowlist + binary blocking, notebook guardrails, injection‑aware prompts
- **Extras:** MMR re‑ranking, session export to Markdown, analytics (latency/tokens/est. cost)

---

## Demo

<p align="center">
  <video src="assets/SageVault_Demo.mp4" width="720" controls muted playsinline>
    Your browser does not support the video tag. <a href="assets/SageVault_Demo.mp4">Download the demo</a>.
  </video>
</p>

---

## Quick Start (3–5 minutes)

### 1) Install
```bash
# Clone
git clone https://github.com/mwill20/SageVault.git
cd SageVault

# Create & activate a virtual env
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2) Configure keys (kept in session only)
```bash
cp .env.example .env
# Edit .env and paste your provider API key(s).
# Optional: add a GitHub token to raise API rate limits.
```

### 3) Run the app
```bash
streamlit run streamlit_app_clean.py
```

### (Optional) Enable LangChain retriever for review
```bash
# Sidebar has a checkbox, OR set an env var:
export SAGEVAULT_USE_LANGCHAIN=1   # enable
# export SAGEVAULT_USE_LANGCHAIN=0 # disable
```

Pick a provider, choose **Repo** or **Documents**, index, and ask questions.

---

## Usage Notes

- **Single source per session:** choose **Repo** *or* **Documents** (not both at once).
- **Supported files:** common code/text/Markdown formats, selected PDFs/Docs; unsafe/binary files are blocked by default.
- **Analytics:** the sidebar shows latency, token counts, and **estimated** cost (for transparency only).

**Sample corpus & script**
```bash
# Try the tiny fixtures and see expected hits in logs
python examples/run_sample.py
```

**Expected outputs (so reviewers can verify)**
- Query: “Where are tests defined?” → sources include `examples/fixtures/fastapi-mini/tests/...`
- Query: “How is the auth header used?” → sources include `examples/fixtures/api-excerpt/...`

---

## How it Works (at a glance)

```mermaid
flowchart LR
  A[Source (Repo or Docs)] --> B[Safety Gate\n(allowlist, size caps,\nblock unsafe binaries)]
  B --> C[Chunker\n(size & overlap sliders)]
  C --> D[Embeddings → Chroma]
  D --> E[Retrieval\n(cosine search)]
  E --> F[MMR Re-ranking\n(diversity)]
  F --> G[LLM Answer\n(citations + sources)]
  G --> H[Export Markdown / Analytics]
```

---

## Known Limitations & Trade-offs

- One source per session (repo **or** docs).
- No remote code execution.
- GitHub token is optional but helps avoid rate limits.
- Cost metrics are **estimates** and may differ from provider billing.

---

## Testing

```bash
pytest -q
```
For reviewers, baseline evidence is stored under `evidence/` and `artifacts/` (session export).

---

## Security

- Keys remain in session memory; never written to disk by the app.
- Blocklist/allowlist for file types; guardrails for risky content.
- “Accept risk” override is available (off by default).

See **security.md** for details and scope.

---

## Documentation

- **QA / Evaluation:** `docs/QA.md` (precision@K snapshot and method)  
- **Publication text:** `docs/publication.md` (paste‑ready for Ready Tensor)  
- **Examples & fixtures:** `examples/` (mini FastAPI repo, API excerpt)  
- **Evidence:** `evidence/` (baseline, pytest) and `artifacts/sample_session.md`  
- **Contributing:** `CONTRIBUTING.md` • **Code of Conduct:** `CODE_OF_CONDUCT.md` • **Changelog:** `CHANGELOG.md`

---

## Support

Open an issue: <https://github.com/mwill20/SageVault/issues>

---

## License

MIT — see `LICENSE`.

---

### Checklist (things to replace on your end)

- [ ] Replace `docs/demo.gif` with the real 45–60s walkthrough GIF
- [ ] Replace `YOUTUBE_URL` above (or remove the video line if not needed)
- [ ] Verify the two **Expected outputs** match your local run
- [ ] Optional: add a screenshot at `assets/analytics_sidebar.png` and reference it in your README if desired

---

### Credits

SageVault pairs a simple, teachable RAG pipeline with pragmatic safety defaults and clear transparency. If any term is new, just start the app—the UI guides you step‑by‑step.
