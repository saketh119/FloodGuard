# FloodGuard — 2-Hour Vertical Slice Build Plan

**Goal:** one demoable end-to-end system — mock IMD data flows into a real database,
becomes correlated flood events, gets an ML risk score and a Gemini-written summary,
and the existing React dashboard reads all of it from a real backend.

**Decisions taken (2026-08-29):** Gemini for the LLM · full vertical slice · fast no-OCR RAG re-ingest.

---

## Starting point

| Area | State before this build |
|---|---|
| `dashboard/` | **Done.** React 19 + Vite, 9 pages, 30s polling. Was talking only to the mock server. |
| `apps/mock-imd/mock_imd_server.py` | **Done.** 9 IMD endpoints, Assam/Kerala flood scenarios. |
| `rag/` | CLI only. No `chroma_db` in repo, deps not installed, no `.env`. |
| `backend/` | **Empty** (`.gitkeep`). No API, no DB, no engines. |
| `ml/` | 5 raw CSVs, empty notebooks, no trained model. |

The frontend being finished is what makes 2 hours plausible — the whole budget goes to the backend.

---

## Timebox

### T+0:00 – 0:15 · Foundations
- Python 3.11 venv, `apps/api/requirements.txt`, `npm install` (both in parallel).
- Package skeleton, `core/config.py` (env-driven), `core/database.py` (SQLite + SQLAlchemy 2.0), logging.

### T+0:15 – 0:45 · Ingestion + event engine
- `flood/adapters/imd_adapter.py` — normalizes all 6 mock IMD shapes into two immutable
  observation tables. Raw JSON is never discarded.
- `flood/collectors/imd_collector.py` — httpx fan-out, content-hash dedupe on insert.
- `flood/engine/triggers.py` — IMD colour codes (Orange/Red) + IMD rainfall thresholds
  (64.5 / 115.6 / 204.5 mm) + basin QPF bands.
- `flood/engine/correlation.py` — district + 6h window match → attach evidence and raise
  confidence, else open a new event. Events evolve; observations stay immutable.
- `scheduler.py` — APScheduler, 60s in dev.
- Routes: `/health` `/events` `/events/{id}` `/stations` `/observations` `/ingest/run`.

### T+0:45 – 1:10 · ML prediction
- `services/ml/training/train_flood_risk.py` — RandomForest on `flood_risk_india.csv` (10k labeled rows),
  stratified split, persisted with metrics to `services/ml/models/`.
- `services/prediction_service.py` + `/predictions` — scores live events from ingested features.
  **Honest gap:** river discharge / water level have no live source (CWC not wired), so those
  features are median-imputed and this is stated in the API response, not hidden.

### T+1:10 – 1:40 · RAG + Gemini
- `services/rag/fast_ingest.py` — PyMuPDF text extraction over the 8 NDMA/IMD PDFs → chunk → Chroma
  (built-in ONNX MiniLM, no torch). Skips OCR and chart captioning by design.
- `services/llm.py` — Gemini via REST (`generativelanguage.googleapis.com`), model from env.
- `/chat` — retrieve top-k → Gemini answer **with citations**. Falls back to extractive
  passages if `GEMINI_API_KEY` is absent, so the demo never hard-fails.
- `/events/{id}/summary` — Gemini writes the evolving `ai_summary` from attached evidence.

### T+1:40 – 2:00 · Wire the dashboard + smoke test
- `lib/api.js`, `.env.local` for `FLOODGUARD_API_BASE`.
- `ChatAssistant` → real `/chat` (delete the canned-answer fallback path).
- Current Floods → real `/events`; Predictions → real `/predictions`.
- Run all three processes, verify the full path end to end.

---

## Explicitly out of scope for these 2 hours
CWC scraper · RSS/news adapter · PostgreSQL + pgvector · auth · Docker · Leaflet maps ·
notifications · the OCR/vision ingest path. All remain in `project_status.md` as backlog.

## Definition of done
Mock IMD → DB → triggers → correlated event → ML score → Gemini summary → visible in the
browser, with `/chat` answering from the NDMA/IMD PDFs and citing them.
