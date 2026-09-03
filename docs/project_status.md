# FloodGuard — Project Status & Roadmap

This document outlines the current state of the **FloodGuard** (AI-Powered Flood Intelligence Platform) project, analyzing the requirements in [application_design_architecture.md](application_design_architecture.md) and [Flood_Intelligence_Project_Architecture.md](Flood_Intelligence_Project_Architecture.md).

---

## 1. Project Vision & Architecture Overview
FloodGuard is designed to be an end-to-end, production-style Flood Intelligence Platform that:
1. **Ingests** hydrological and meteorological data from:
   - India Meteorological Department (IMD) - Warnings and rainfall observations.
   - Central Water Commission (CWC) - Water level measurements and forecasts.
   - Weather APIs - Temperature, humidity, pressure, wind, and local precipitation.
   - RSS / News Feeds - Newspaper articles and disaster warnings.
2. **Processes** raw ingestion into structured observation tables.
3. **Detects Triggers** (alerts) based on source-specific rule thresholds.
4. **Correlates Events** across multiple sources (location + time matching) to define single, evolving "Flood Events" rather than disconnected observation points.
5. **Predicts Risk & Summarizes** using ML Models (prediction engine) and LLMs (AI summarizer/RAG).
6. **Visualizes** events and predictions on a web-based Next.js dashboard featuring Leaflet maps and interactive tools.

---

## 2. Where We Are (Current Status)

The project is currently in the **early development and indexing phase**:
* **Designed & Planned**: The high-level and detailed software architectures, database design concepts, event correlation engines, and REST endpoints are fully detailed in the architecture docs.
* **Core RAG System Built**: The RAG (Retrieval-Augmented Generation) pipeline is completed and ready under the [rag](rag) folder, which ingests official guidelines and allows local semantic query search against a local database.
* **Placeholder Directories**: Folders for the `backend`, `frontend`, `ml`, and `scripts` are created, but they only contain boilerplate files or initial data notebooks.

---

## 3. What's Done

### 📂 Datasets & Documents
- **Reference Materials Ingested**: Added essential regulatory and operational flood PDFs inside [data/rag/](data/rag/):
  - **IMD**: SOPs, Weather Forecast Bulletins, Early Warning Guidelines.
  - **NDMA**: Flood Management, Flood Plain Zoning, Urban Flooding, and Community DRR Guidelines.
  - **Reference**: Flood Response Reference Guides.

### 🧠 Retrieval-Augmented Generation (RAG) Module
- **Ingestion Pipeline**: Created [ingest.py](services/rag/ingest.py) utilizing the `unstructured` package.
  - Features high-resolution OCR parsing via Tesseract/Poppler.
  - Formats tables using direct HTML representation.
  - Integrates an OpenRouter Vision LLM to automatically generate textual descriptions for charts/maps.
  - Generates 384-dimensional local sentence embeddings using `all-MiniLM-L6-v2` and persists them in a local ChromaDB instance inside [services/rag/chroma_db/](services/rag/chroma_db).
- **Interactive CLI Query Application**: Created [app.py](services/rag/app.py) enabling full conversational Q&A against the guidelines database using the free `tencent/hy3:free` model on OpenRouter.
- **RAG Architecture Documentation**: Fully documented in [rag_ARCHITECTURE.md](rag/rag_ARCHITECTURE.md) and [rag_SETUP_GUIDE.md](rag/rag_SETUP_GUIDE.md).

### 🛠️ Development & Mock Utilities
- **Mock IMD API Server**: Created [mock_imd_server.py](apps/mock-imd/mock_imd_server.py) using FastAPI to replicate real IMD endpoints (warnings, precipitation forecasts, station forecasts, current weather metrics, and AWS data) returning realistic mock datasets (including extreme weather warning scenarios in Assam/Kerala) for prototype development.

### 📓 ML Data Exploration
- Skeleton notebooks created in [services/ml/notebooks/](services/ml/notebooks/):
  - `01_data_exploration.ipynb`
  - `02_preprocessing.ipynb`
  - `03_model_training.ipynb`

---

## 3b. Built in the 2-Hour Vertical Slice (2026-08-29)

See [BUILD_PLAN.md](BUILD_PLAN.md) for the plan and [RUNNING.md](RUNNING.md) to run it.

### 🧱 Backend (was empty, now a working service)
- **FastAPI gateway** at `apps/api/app/` — SQLite via SQLAlchemy 2.0, env-driven config, CORS.
- **Schema implemented**: `imd_observation`, `station`, `flood_event`, `event_evidence`,
  `prediction_result`. Observations are immutable and keep their raw JSON; events are derived.
- **IMD adapter** normalises all six mock endpoint shapes into one observation record, with a
  content hash so a 60s re-poll of unchanged data does not duplicate rows.
- **Trigger engine** using IMD's own thresholds — colour codes ≥ Orange, and the
  64.5 / 115.6 / 204.5 mm rainfall classification.
- **Correlation engine** — district + 6h window match attaches evidence and raises confidence,
  otherwise opens a new event. Contributions have **diminishing returns per evidence type**, so
  one basin forecast split across four sub-basins counts as one signal, not four.
- **APScheduler** collecting every 60s; verified firing unattended.
- **Endpoints**: `/health` `/events` `/events/{id}` `/events/{id}/summary` `/stations`
  `/observations` `/predictions` `/predictions/run` `/predictions/model` `/chat` `/ingest/run`.

### 🤖 ML
- `services/ml/training/train_flood_risk.py` — trained on `flood_risk_india.csv` and **rejected**:
  ROC-AUC **0.496** (chance) with near-uniform feature importances. The script is kept as the
  evidence for that decision. That dataset's labels do not relate to its features.
- `services/ml/training/train_flood_severity.py` — **the served model**. IndoFloods, 4,548 real gauged
  events across 155 catchments, predicting escalation to `Severe Flood` from antecedent rainfall.
  **GroupKFold-by-gauge ROC-AUC 0.575** (0.611 with catchment attributes, which we cannot yet
  resolve live). Modest but real. The rule-based IMD index drives the headline risk score;
  the model contributes 25% of the blend.
- `/predictions` reports `feature_provenance` per feature — observed, interpolated or imputed.

### 🧠 RAG
- `services/rag/fast_ingest.py` — OCR-free PyMuPDF extraction, **2,677 chunks from all 8 PDFs**,
  embedded with Chroma's bundled ONNX MiniLM. No torch, no API key, ~2 min.
- `/chat` retrieves top-k and grounds a Gemini answer with `[Title, p.N]` citations.
  Without a key it returns the source passages verbatim, labelled as unsummarised.
- AI event summaries regenerate from the evidence trail as evidence accumulates.
- **Hybrid retrieval**: vector search + a keyword pass over salient query terms, merged
  and re-scored, then filtered for near-duplicates and per-document dominance. Needed
  because government PDFs reprint the same footer on every page — pure vector search
  returned four copies of one disclaimer and missed IMD SOP Table 1.11, which actually
  defines the colour codes.
- **Gemini failures are visible**: the client surfaces Google's own error text and tags
  the reason (`bad_key`, `bad_model`, `rate_limited`, `blocked`, …), retries transient
  5xx/429, and the chat UI shows a red banner. A configured-but-broken key no longer
  looks the same as no key.
- `GET /llm/check` makes one real call; `python run.py doctor` uses it and compares key
  fingerprints to catch the case where `.env` was edited under a running server.

### 🖥️ Dashboard
- `services/floodguardService.js` + `hooks/useFloodEvents.js` — client for the new backend.
- **Chat Assistant now talks to the real RAG service.** The hardcoded canned-answer fallback
  has been deleted; answers show their source documents and pages.
- **Correlated Flood Events** section on Current Floods — expandable rows showing risk,
  confidence, ML probability and the full evidence trail behind each event.

### Verified end to end
`34 observations → 19 triggers → 4 correlated events → ML scored → summarised → visible in UI`,
with the scheduler running unattended and all three services talking to each other.

### 🌦️ Live data + realtime (added after the initial slice)
- **OpenWeather integration** — `apps/api/app/flood/adapters/openweather_adapter.py` and a
  matching collector fetch observed conditions and a 5-day forecast for all 7 districts
  each cycle (14 calls, inside the free 60/min limit). This is the platform's first
  genuinely live source.
- New trigger rules: observed rain at or above a quarter of the IMD heavy-rain figure
  (rates, not daily totals), and next-24h forecast accumulation against the full IMD
  daily thresholds. Verified across all severity bands.
- **Server-sent events** at `GET /stream`. The pipeline publishes on cycle completion and
  the dashboard refreshes immediately; a 60s poll remains as a fallback. The header shows
  live/reconnecting state.
- `GET /dashboard/{district}` now carries a `live` block and forecast accumulations.

### 🖥️ Interface
- Removed the fake account chip ("Saketh", avatar, Logout) and the dead Settings link —
  there is no auth layer, so they were decoration. The header slot now shows feed
  connection state and data age; the sidebar footer shows which sources are live versus
  mocked.
- Removed the "Nearby Shelters — user input needed" placeholder card, replaced with real
  24h/72h rain forecast.
- Live figures carry a `LIVE` badge, so a real OpenWeather reading is never presented
  with the same authority as a mocked IMD one.
- Fixed dead references left by the Next.js port (`LOCATIONS`, `onLocationChange`) and
  the missing `coords` field; removed emoji and build commands from product copy.

### 🐛 Chat fixes
- `POST /chat` required a 3-character question, so typing "Hi" returned HTTP 422. The
  floor is now 1 — rejecting a greeting with a validation error is a worse answer than
  replying to it.
- Greetings and pleasantries ("hi", "thanks", "ok", "namaste") now get a short
  capability reply instead of a document search. Running retrieval on "hi" returns
  whichever passage is least dissimilar to it, which reads as broken.
- The chat UI rendered FastAPI validation errors as `[object Object]` — `detail` is an
  array of objects, not a string — and labelled every failure "Could not reach the API"
  even when the API had answered with an error status. Both fixed: errors are formatted
  by shape, and "unreachable" is now claimed only when there is genuinely no response.

### 📍 Dynamic locations
The district registry was a hardcoded list of 7 in `geo.py`, seeded from the districts
the IMD mock serves. That was the right shape when IMD was the only source; OpenWeather
works at any coordinate, so the limit had become artificial.

- `GET /districts/search?q=` geocodes any place through OpenWeather.
- `POST /districts/track` follows it; a new `tracked_location` table persists the choice
  and the collector picks it up on the next cycle automatically.
- `GET /districts` returns built-ins and tracked locations together, each flagged `imd`.
- Correlation trusts an observation's own coordinates when it carries them, so tracked
  places flow through the event engine without being in the static registry.
- Tracked locations get live weather but no IMD warnings. `/dashboard` nulls the IMD
  slots and sets `imd_covered: false`, and the UI marks them "Live weather only" —
  otherwise an empty IMD panel reads as data that has not arrived yet.

### 📍 Geolocation and picker fixes
- **"Use my location" reported the wrong place.** It snapped a GPS fix to the nearest
  already-followed location, so a user in Telangana was shown Kerala — the closest known
  point, and wrong. It now reverse-geocodes the actual coordinates via
  `GET /districts/reverse`, follows that place if new, and switches to it.
- **The picker was unstyled.** The Next.js port renamed the component's class names but
  the stylesheet still carried the originals, so 14 of 22 `styles.*` lookups resolved to
  `undefined` and the bar rendered as unspaced runtogether text. Stylesheet rewritten
  against the actual markup; a class-coverage check now passes.
- Removed the duplicate location banner — `LocationBar` and `Dashboard` were each
  rendering their own, showing the district and coordinates twice.
- Geolocation errors are now distinguished (permission denied / unavailable / timeout)
  instead of one generic failure.

### 📈 Flood Risk Prediction fixes
- **Every row showed the same date.** IMD's basin QPF response is a list of SUB-BASINS,
  each carrying `Day1…Day5` and all sharing one issue date. The derive layer iterated
  sub-basins and read `Day{i+1}` from each — mixing two dimensions, so it displayed
  Lohit's day 1, Dibang's day 2 and so on, every row stamped with the same issue date.
  QPF is now expanded across days and reduced across sub-basins (worst per day, the
  right reading for a basin-wide warning).
- **Tracked locations had no forecast at all.** The panel was driven solely by IMD basin
  QPF, which does not exist outside IMD's districts, so Hyderabad and Vijayawada showed
  "No forecast data available". OpenWeather's per-day accumulation is now the base
  series — real data, available at any coordinate — with IMD QPF overlaid where it
  exists. The higher figure wins, since under-stating flood risk is the costlier error.
- Risk percentages are interpolated along IMD's daily rainfall classification
  (64.5 / 115.6 / 204.5 mm) rather than jumping between buckets, and each row now shows
  the millimetres and its source, because a derived index is not readable on its own.
- Fixed a timezone bug: `toISOString()` converted local midnight to UTC and shifted the
  day back, stamping a forecast issued on the 29th as the 28th.

### ⚡ Current Floods realtime gap
The page's top section was already on the SSE path via the shared context, but the
**Correlated Flood Events** panel below it ran its own 60s poll and ignored the stream —
so that half of the page could be a minute behind the half above it. The context now
publishes a `cycle` counter from the single shared EventSource, and `useFloodEvents`
refetches on it. One connection still serves everything: browsers cap concurrent
connections per origin, so opening a second EventSource per component would be wasteful.
The interval remains only as a fallback for when the stream is down.

Verified end to end: with a district switched to Red in the mock source, the 60s
scheduler detected it unattended, opened a `severe`/`active` event at 0.98 confidence
from three independent pieces of evidence (nowcast, 5-day warning, district rainfall),
scored it, wrote a Gemini summary, and announced it on the stream — pushed 0.42s after
a cycle began.

## 4. What's Left (Backlog)

### 🧱 1. Backend Ingestion & Database Layer
- [ ] **Database Setup**: Implement the relational schema outlined in SADD (SQLite or PostgreSQL) containing:
  - `imd_observation`
  - `cwc_station` (metadata) & `cwc_measurement` (time-series)
  - `weather_observation`
  - `news_observation`
  - `flood_events` & `event_evidence`
  - `prediction_results` & `notifications`
- [ ] **Source Adapters**:
  - IMD Adapter (warning & rainfall data scraper).
  - CWC Scraper utilizing the reverse-engineered `GET /iam/api/layer-station/{stationCode}` API.
  - Weather API client wrapper.
  - RSS News scraper.
- [ ] **Data Ingestion Scheduler**: Build the scheduler module (e.g. APScheduler or Celery) configured to pull data periodically (IMD: 5 min, Weather: 10 min, News: 30 min).

### ⚙️ 2. Core Processing Engines
- [ ] **Trigger Detection Engine**: Set up source-specific detection filters (e.g., Red/Orange IMD warnings, water level exceeding warning/danger limits on CWC, rainfall volume thresholds).
- [ ] **Event Correlation Engine**: Write logic to match incoming alerts to existing events within spatial/temporal windows, updating the event's confidence score and linking the new alert as evidence.
- [ ] **AI Summarizer**: Implement an LLM pipeline to periodically update the unified event description (`ai_summary` field) as new evidence gets attached.
- [ ] **ML Prediction Engine**: Code the ML pipeline to predict severity and probability scores based on meteorological models.

### 🌐 3. FastAPI REST APIs
- [ ] Build FastAPI server with endpoints for:
  - `/events` (GET filters, POST/PUT adjustments)
  - `/stations` (GET location coordinates)
  - `/predictions` (GET scores and trends)
  - `/chat` (Integrate the existing RAG Q&A console into an API endpoint)

### 🖥️ 5. Frontend Dashboard (Next.js)
- [ ] **Interactive Map View**: Implement a map (Leaflet/Mapbox) rendering stations, river layers, flood zones, and clickable markers with dynamic coloring (based on hazard status).
- [ ] **Event Timeline & Feed**: Component highlighting active flood events, historical progression, and correlated raw evidence.
- [ ] **AI Chat Console**: Integrate the RAG chatbot interface directly into the web dashboard.
- [ ] **Prediction Dashboard**: Panels showing prediction trends, risk factors, and notifications.
