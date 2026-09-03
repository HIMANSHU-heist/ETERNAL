# Analyzer AI

**Chat with your data. Any format, any size — upload it, ask questions, get analysis, predictions, and reports, powered by autonomous AI agents.**

Analyzer AI is a full-stack, agentic AI platform that acts like a data analyst and data scientist rolled into one. Upload a dataset (CSV, Excel, JSON, Parquet, and more) and chat with it in plain language — Analyzer AI understands the schema, runs exploratory analysis, engineers features, trains predictive models, and generates dashboards and reports, all through a conversational interface backed by a multi-agent orchestration layer.

## What it does
- **Universal ingestion** — CSV, XLSX, JSON, Parquet, TSV (more formats coming)
- **Chat-driven analysis** — ask "what's driving churn in this data" and get a real answer, grounded in your actual dataset
- **Agentic pipeline** — a planner agent breaks down your goal, specialized agents handle EDA, feature engineering, modeling, and reporting
- **AutoML + explainability** — baseline models trained automatically, with SHAP-based explanations
- **Auto-generated reports** — dashboards, charts, and downloadable summaries

## Tech stack
| Layer | Tech |
|---|---|
| Backend API | FastAPI |
| Data processing | pandas, DuckDB |
| Agent orchestration | LangGraph / CrewAI |
| ML / AutoML | scikit-learn, PyCaret |
| Frontend | Streamlit (MVP) → React (production) |
| Dev environment | GitHub Codespaces |
| Heavy compute / training | Kaggle Notebooks |
| Deployment | Docker, cloud (AWS/GCP/HuggingFace Spaces) |

## Project structure
```
analyzer-ai/
├── .devcontainer/     # GitHub Codespaces auto-setup
├── backend/           # FastAPI app (ingestion, chat, agents, ML)
├── frontend/          # (coming soon)
└── notebooks/         # Kaggle-ready notebooks for model experimentation
```

## Getting started (GitHub Codespaces)
1. Click **Code → Codespaces → Create codespace on main**
2. Wait for the container to build (auto-installs backend dependencies)
3. Run the backend:
   ```bash
   cd backend
   uvicorn app.main:app --reload --port 8000
   ```
4. Open the forwarded port 8000 → `/docs` for the Swagger UI

## Roadmap
- [x] Step 1 — Universal file upload + schema detection
- [ ] Step 2 — Chat endpoint (LLM-powered Q&A over your dataset)
- [ ] Step 3 — Agentic orchestration (planner + specialist agents)
- [ ] Step 4 — AutoML + feature engineering + explainability
- [ ] Step 5 — Dashboard UI + report export
- [ ] Step 6 — Production deployment (Docker, CI/CD, monitoring)

## License
MIT
