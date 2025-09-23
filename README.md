---
title: Github Guidebot Mvp
emoji: 🚀
colorFrom: red
colorTo: red
sdk: docker
app_port: 8501
tags:
  - streamlit
pinned: false
short_description: Streamlit template space
---

# GitHub GuideBot — MVP v1

Learn GitHub by doing. This MVP is a demo locked to the GuideBot repo: it generates a step-by-step walkthrough with copyable commands, citation chips, and safety warnings, plus a three-stop Repo Tour.

## What’s inside
- **Coach Mode:** Numbered checklist (clone → install → run → verify).
- **Repo Tour:** README → Dependencies → Entrypoint, with short blurbs.
- **Safety Gate:** Commands are scored/redacted; risky patterns surface warnings.

## Run locally
```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .\.venv\Scripts\Activate.ps1
pip install -U pip -r requirements.txt
DEMO_MODE=1 streamlit run app/streamlit_app.py

