# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A single-file Streamlit dashboard (`app.py`) with four financial calculator tabs: Compound Interest, SIP / Regular Contributions, Goal Planner, and Mortgage Calculator. The app is **fully stateless** — no database, no `st.session_state`, no external APIs, no file writes, no background threads. All computation is pure arithmetic on widget inputs, rendered with Plotly.

## Common commands

```bash
# Run locally
pip install -r requirements.txt
streamlit run app.py            # opens at http://localhost:8501

# Container build / smoke test
docker build -t calx .
docker run -p 8501:8501 calx
```

There is no test suite, no linter config, and no build step beyond Docker.

## Code structure

`app.py` is the entire application. Each of the four tabs is a self-contained block delimited by `# --- Tab N: ... ---` comments — they share no state and can be edited independently. Pattern within each tab: a left input column (`st.number_input` / `st.slider` / `st.selectbox`), a right column with one or more Plotly charts, then a row of `st.metric` cards. Widget keys are namespaced per-tab (`sip_principal`, `sip_rate`, `goal_rate`, etc.) to avoid collisions between tabs that ask for similar inputs.

When adding a new calculator, follow the same structure: add a tab to the `st.tabs([...])` call at the top, then add a `with tabN:` block with the input/chart/metrics layout.

## Deployment

Deploys to **Google Cloud Run** at https://calx.portfola.net via `.github/workflows/deploy.yml` on every push to `main`. CI uses GCP Workload Identity Federation (no static keys). DNS for the custom domain lives in AWS Route53 (CNAME → `ghs.googlehosted.com`).

The full one-time GCP bootstrap (project, Artifact Registry, service account, WIF pool/provider, Cloud Run service, domain mapping, GitHub repo variables) is documented in `README.md` under "One-time GCP bootstrap". When making deployment-related changes, edit those `gcloud` snippets in the README rather than creating separate docs.

**Important context for any "let's switch to AWS" discussion:** AWS App Runner stopped accepting new customers on 2026-04-30. ECS Express Mode (AWS's recommended replacement) auto-provisions an ALB with a ~$16/mo idle floor — a cost regression vs. Cloud Run's free tier for a personal calculator.

## Streamlit-on-Cloud-Run gotchas

- Streamlit uses WebSockets for widget updates. The Cloud Run service is deployed with `--timeout=3600` so sessions can live up to an hour; longer sessions just need a browser refresh (the app is stateless).
- Container listens on port 8501 (not Cloud Run's default 8080). The deploy command sets `--port=8501` explicitly.
- `--min-instances=0` enables scale-to-zero. Cold start is ~1–3s.
