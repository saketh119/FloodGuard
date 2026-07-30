# FloodGuard — Project Status & Roadmap

This document outlines the current state of the **FloodGuard** (AI-Powered Flood Intelligence Platform) project, analyzing the requirements in [application_design_architecture.md](file:///d:/FloodGuard/application_design_architecture.md) and [Flood_Intelligence_Project_Architecture.md](file:///d:/FloodGuard/Flood_Intelligence_Project_Architecture.md).

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
* **Core RAG System Built**: The RAG (Retrieval-Augmented Generation) pipeline is completed and ready under the [rag](file:///d:/FloodGuard/rag) folder, which ingests official guidelines and allows local semantic query search against a local database.
* **Placeholder Directories**: Folders for the `backend`, `frontend`, `ml`, and `scripts` are created, but they only contain boilerplate files or initial data notebooks.

---

## 3. What's Done

### 📂 Datasets & Documents
- **Reference Materials Ingested**: Added essential regulatory and operational flood PDFs inside [datasets/rag/](file:///d:/FloodGuard/datasets/rag/):
  - **IMD**: SOPs, Weather Forecast Bulletins, Early Warning Guidelines.
  - **NDMA**: Flood Management, Flood Plain Zoning, Urban Flooding, and Community DRR Guidelines.
  - **Reference**: Flood Response Reference Guides.

### 🧠 Retrieval-Augmented Generation (RAG) Module
- **Ingestion Pipeline**: Created [ingest.py](file:///d:/FloodGuard/rag/ingest.py) utilizing the `unstructured` package.
  - Features high-resolution OCR parsing via Tesseract/Poppler.
  - Formats tables using direct HTML representation.
  - Integrates an OpenRouter Vision LLM to automatically generate textual descriptions for charts/maps.
  - Generates 384-dimensional local sentence embeddings using `all-MiniLM-L6-v2` and persists them in a local ChromaDB instance inside [rag/chroma_db/](file:///d:/FloodGuard/rag/chroma_db).
- **Interactive CLI Query Application**: Created [app.py](file:///d:/FloodGuard/rag/app.py) enabling full conversational Q&A against the guidelines database using the free `tencent/hy3:free` model on OpenRouter.
- **RAG Architecture Documentation**: Fully documented in [rag_ARCHITECTURE.md](file:///d:/FloodGuard/rag/rag_ARCHITECTURE.md) and [rag_SETUP_GUIDE.md](file:///d:/FloodGuard/rag/rag_SETUP_GUIDE.md).

### 🛠️ Development & Mock Utilities
- **Mock IMD API Server**: Created [mock_imd_server.py](file:///d:/FloodGuard/scripts/mock_imd_server.py) using FastAPI to replicate real IMD endpoints (warnings, precipitation forecasts, station forecasts, current weather metrics, and AWS data) returning realistic mock datasets (including extreme weather warning scenarios in Assam/Kerala) for prototype development.

### 📓 ML Data Exploration
- Skeleton notebooks created in [ml/notebooks/](file:///d:/FloodGuard/ml/notebooks/):
  - `01_data_exploration.ipynb`
  - `02_preprocessing.ipynb`
  - `03_model_training.ipynb`

---

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
