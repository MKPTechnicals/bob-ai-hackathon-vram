# 🚀 Bobathon Grid Optimiser

Lightweight, realtime grid forecasting and operator briefing prototype that forecasts short-term demand spikes, detects asset anomalies, recommends low-curtailment actions, and generates operator-facing briefs using the Bob AI API.

---

## 👥 Team

| Field | Value |
|---|---|
| **Team Name** | VRAM |
| **Track** | AI / Sustainability |
| **Team Lead** | Aastha Patel — [26pgce014@charusat.edu.in] |
| **Members** | Vaibhavi Bhatt, Ruchit Jivani, Meet K Patel |

---

## 🎯 Problem Statement

Grid operators need fast, reliable short-term forecasts and concise operator instructions to minimise curtailment and avoid manual triage during demand or renewable-output anomalies.

This project demonstrates a compact on-device forecasting pipeline plus anomaly detection and an operator briefing generator to speed decisions.

---

## 💡 Solution Overview

- A compact Liquid State Machine (reservoir) forecaster for low-latency, short-horizon predictions.
- Anomaly detection (IsolationForest) surfaces underperforming assets and timestamps.
- A simple heuristic optimiser recommends actions (curtailment, re-dispatch, battery) ranked by cost/impact.
- Natural-language operator briefs and explanations are generated via the Bob AI wrapper.

Key advantages: small model footprint, real-time WebSocket updates, reproducible demo with synthetic telemetry.

---

## ✨ Key Features

- Short-horizon demand forecasting (hours) using a reservoir LSM (`src/model.py`).
- Per-asset anomaly detection and rudimentary root-cause mapping.
- Heuristic recommender that balances curtailment and operational constraints (`src/optimizer.py`).
- Bob AI integration wrapper for operator briefs (`src/bob_integration.py`) with diagnostic fallbacks.
- Bootstrap dashboard with Chart.js and WebSocket realtime updates (`src/static/*`).

---

## 🛠️ Tech Stack

| Category | Technologies |
|---|---|
| **Languages** | Python 3.12, JavaScript (vanilla) |
| **Backend** | FastAPI, Uvicorn |
| **Frontend** | Bootstrap, Chart.js, WebSockets |
| **ML** | NumPy, scikit-learn (IsolationForest), custom reservoir forecaster |
| **Testing / CI** | pytest, Playwright, GitHub Actions |

---

## 📁 Important Files

- `src/app.py` — FastAPI entrypoint, WebSocket `/ws`, endpoints: `/forecast`, `/anomalies`, `/recommend`.
- `src/model.py` — `LiquidStateForecaster`, `AnomalyDetector` (train/predict/save/load).
- `src/optimizer.py` — Heuristic recommendation logic.
- `src/bob_integration.py` — Bob wrapper and brief-generation helper.
- `src/static/index.html`, `src/static/app.js`, `src/static/styles.css` — Dashboard assets.
- `demo/run_demo.py` — Script that runs a quick forecast/anomaly/recommendation demo.
- `tests/` — Smoke and Playwright tests.

---

## ⚡ Quickstart (local)

Prerequisites: Python 3.11+ (3.12 recommended), Git, and Node if you want to run Playwright tests.

1. Create and activate a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1    # PowerShell
```

2. Install Python dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

3. Environment variables

Set these in your shell or via an `.env` file (do NOT commit secrets):

- `FRONTEND_API_KEY` — optional API key required by the dashboard for WebSocket connect (if used).
- `BOB_API_URL` — Bob API base URL (e.g., `https://api.us-east.bob.ibm.com/inference/v1`).
- `BOB_API_KEY` — Bob API key (keep secret).

Example (PowerShell):

```powershell
$env:FRONTEND_API_KEY='your_frontend_key'
$env:BOB_API_URL='https://api.us-east.bob.ibm.com/inference/v1'
$env:BOB_API_KEY='your_bob_api_key_here'
```

4. Run the API server

```powershell
uvicorn src.app:app --reload --port 8000
```

5. Open the dashboard

Point your browser to: http://localhost:8000/ and click `Connect WS` after entering `FRONTEND_API_KEY` (if set).

6. Run the demo script (optional)

```powershell
python demo/run_demo.py
```

---

## 🧪 Tests

- Run unit/smoke tests:

```powershell
pytest -q
```

- Run Playwright UI tests (requires Playwright browsers installed):

```powershell
playwright install --with-deps
pytest tests/test_ui_playwright.py -q
```

---

## 📌 Bob API Integration Notes & Troubleshooting

- We implemented a robust wrapper (`src/bob_integration.py`) that attempts common endpoint paths and header formats and returns detailed diagnostics when calls fail.
- Known blocking: some environments receive `403` Cloudflare responses from `api.us-east.bob.ibm.com`. If you see HTML 403 pages in test output, try:
	- Running the same `curl`/script from your personal machine (not CI) or a permitted network.
	- Confirming the exact Bob endpoint and header format with your account admin (some Bob deployments require an IAM exchange).
- Example local curl to test access (replace values):

```bash
curl -v -X POST 'https://api.us-east.bob.ibm.com/inference/v1' \
	-H "x-api-key: YOUR_KEY" \
	-H "Content-Type: application/json" \
	-d '{"input":{"text":"hi"},"instruction":"acknowledge"}'
```

If you want, paste the raw response from that curl and I will adapt the wrapper to match the exact header/body shape required.

---

## 🖥️ Demo

| Artifact | Link |
|---|---|
| 📹 Demo Video | [See demo/demo-video-link.txt](demo/demo-video-link.txt) |
| 🌐 Live Demo | [See demo/live-demo-url.txt](demo/live-demo-url.txt) |
| 🖼️ Screenshots | [See demo/screenshots/](demo/screenshots/) |
| 📊 Presentation | [See presentation/slides.pdf](presentation/) |

---

## 🎬 Demo Plan

1. Start the server: `uvicorn src.app:app --reload --port 8000`
2. Open http://localhost:8000/ and connect WebSocket using the `FRONTEND_API_KEY` if configured.
3. Click `Forecast`, `Anomalies`, and `Recommend` to observe Chart.js updates and Bob-generated brief text.

---

## ✅ CI / Deployment notes

- GitHub Actions workflow includes test and Playwright steps. Ensure Playwright browsers are installed in CI or use `playwright install --with-deps` before test step.
- Model persistence: the reservoir model is saved/loaded from disk by `LiquidStateForecaster.save()` / `load()`; ensure the process has write access to the working directory.

---

## Limitations & Known Issues

- Demo uses synthetic telemetry in `src/data.py` for reproducibility — replace with real telemetry for production evaluation.
- Bob API calls may be network-blocked (Cloudflare 403) from some environments; the wrapper logs attempts and fallbacks.
- Recommendations are heuristics (safe for demo). Production requires constrained optimisation and human approval before actuation.

---

## Next steps / Roadmap

- Harden Bob integration with IAM token exchange if required.
- Replace heuristic optimiser with a constrained optimisation solver.
- Add role-based auth and audit logging for operator actions.
- Enhance Playwright CI reliability and add visual regression checks.

---

## Where to look in the repo

- `src/app.py` — run loop, endpoints and WebSocket
- `src/model.py` — forecasting + anomaly detection
- `src/optimizer.py` — recommendations
- `src/bob_integration.py` — Bob API wrapper and brief generation
- `src/static/` — frontend assets
- `demo/run_demo.py` — demo runner

---

## Questions / items I need from you

1. Confirm the preferred **display project title** and the exact **team contact email** to show on the README.
2. Do you want me to include a public link to a deployed demo (if available) in `Live Demo`? If yes, provide the URL.
3. Should I include a short `LICENSE` section and which license do you want (MIT/Apache-2.0/None)?
4. Do you want me to embed any screenshots from `demo/screenshots/` into the README (I can add images if you approve)?

---

## License

Specify a license file or answer question (3) above to include one here.

---

Thank you — I updated `README.md` with the above quickstart and notes. Reply with answers to the questions above and I will finalize the README (add screenshots, license, and any team/contact edits).

