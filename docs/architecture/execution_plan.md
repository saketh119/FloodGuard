# Flood Intelligence Platform – End-to-End Execution Plan

## Project Goal

Build an AI-powered Flood Intelligence Platform that:

* Collects flood-related information from multiple sources
* Processes and normalizes the data
* Stores structured flood events
* Allows users to search by location
* Generates AI summaries
* Provides flood predictions
* Answers flood-related questions using RAG

---

# Overall System Architecture

```
                            USER
                              │
                              ▼
                     Next.js Frontend
                              │
                    REST API / WebSocket
                              │
                              ▼
                     FastAPI Backend
                              │
      ┌───────────────┬───────────────┬───────────────┐
      │               │               │               │
      ▼               ▼               ▼               ▼
 Flood Service    AI Service    Prediction     Authentication
                                 Service
```

---

# Complete Data Flow

```
                IMD API
                   │
                CWC API
                   │
              Weather API
                   │
               News RSS
                   │
         (Future: Social Media)
                   │
                   ▼
             Source Adapters
                   │
                   ▼
             Normalization
                   │
                   ▼
              Validation
                   │
                   ▼
              Enrichment
                   │
                   ▼
         Duplicate Detection
                   │
                   ▼
         Flood Event Database
                   │
        ┌──────────┴───────────┐
        │                      │
        ▼                      ▼
 Search Service         AI Summarizer
        │                      │
        └──────────┬───────────┘
                   ▼
                Frontend
```

---

# Development Phases

---

# Phase 1 — Project Foundation

Goal:

Create the basic backend and frontend structure.

Tasks

* Create FastAPI backend
* Create Next.js frontend
* Configure PostgreSQL
* Dockerize services
* Setup environment variables
* Logging
* Configuration management

Deliverable

```
Frontend

↓

FastAPI

↓

PostgreSQL
```

No intelligence yet.

---

# Phase 2 — Mock API Layer

Since IMD/CWC approval is pending:

Create fake APIs.

```
GET /mock/imd

GET /mock/cwc

GET /mock/weather

GET /mock/news
```

Every endpoint returns realistic JSON.

Store mock responses in

```
mock_data/

imd/

cwc/

weather/

rss/
```

Deliverable

Backend behaves exactly like production.

---

# Phase 3 — Source Adapters

Every source has different JSON.

Create adapters.

```
IMD JSON
        │
        ▼
IMD Adapter
        │
        ▼
Standard Flood Event
```

Same for

```
CWC

RSS

Weather
```

The rest of the application should never know where the data came from.

---

# Phase 4 — Data Preprocessing

This is the most important phase.

Pipeline

```
Raw API

↓

Normalize

↓

Validate

↓

Enrich

↓

Deduplicate

↓

Store
```

Normalization

* Standard district names
* Standard timestamps
* Standard units
* Standard severity
* Standard coordinates

Validation

* Missing fields
* Invalid timestamps
* Invalid coordinates

Enrichment

* Geocoding
* Reverse geocoding
* Confidence score
* Derived district/state

Deduplication

Merge

IMD

*

News

*

RSS

into one event if appropriate.

---

# Phase 5 — Database Design

Suggested tables

```
flood_events

weather_observations

river_levels

reservoir_levels

alerts

stations
```

Future tables

```
users

saved_locations

notifications
```

---

# Phase 6 — Scheduler

Instead of fetching data only when users search,

run collectors every few minutes.

```
Scheduler

↓

Fetch APIs

↓

Process

↓

Store
```

Now searching becomes very fast.

---

# Phase 7 — Search Engine

User chooses

```
Location

Time Range

Severity

Category
```

Backend

```
SQL

↓

Matching Flood Events

↓

Return JSON
```

Example

```
Vijayawada

Last 24 Hours

Road Closures
```

---

# Phase 8 — AI Summarization

Suppose database returns

```
25 events
```

AI produces

```
Summary

Important alerts

Key risks

Recommendations
```

Instead of reading 25 records,

users read one summary.

---

# Phase 9 — RAG

Knowledge Base

```
NDMA PDFs

Flood Manuals

Preparedness Guides

Evacuation Procedures
```

Pipeline

```
PDF

↓

Chunking

↓

Embedding

↓

Chroma

↓

Retriever

↓

LLM
```

Chatbot now answers

"How should I prepare for flooding?"

instead of live questions only.

---

# Phase 10 — Hybrid AI

Question

```
Will Vijayawada flood tomorrow?
```

Backend gathers

```
Weather

+

River Level

+

Current Alerts

+

Relevant Documents
```

↓

LLM

↓

Final Answer

This is much stronger than standalone RAG.

---

# Phase 11 — Flood Prediction

Input

```
Rainfall

River Level

Reservoir Data

Historical Data

Weather Forecast
```

↓

ML Model

↓

Flood Probability

↓

Store Prediction

---

# Phase 12 — Interactive Dashboard

Dashboard

```
Current Alerts

River Levels

Rainfall

Flood Prediction

Latest News

AI Summary
```

Maps

```
Flood Events

Shelters

River Stations

Weather Stations
```

---

# Complete Folder Structure

```
backend/

core/
    config.py
    database.py
    logger.py
    geocoding.py

flood/

    adapters/
        imd_adapter.py
        cwc_adapter.py
        weather_adapter.py
        rss_adapter.py

    collectors/
        imd_collector.py
        cwc_collector.py
        weather_collector.py
        rss_collector.py

    preprocessing/
        normalizer.py
        validator.py
        enricher.py
        deduplicator.py

    services/
        search_service.py
        summary_service.py
        flood_event_service.py
        prediction_service.py

    scheduler/

    routes/

    models/

    mock_data/

rag/

prediction/

frontend/
```

---

# Execution Timeline

```
Week 1
--------
Project setup
Database
Docker
Mock APIs

Week 2
--------
Adapters
Normalization
Validation

Week 3
--------
Scheduler
Collectors
Database ingestion

Week 4
--------
Search APIs
Frontend integration

Week 5
--------
RAG integration
Chatbot

Week 6
--------
AI summaries
Hybrid retrieval

Week 7
--------
Flood prediction
Maps

Week 8
--------
Testing
Optimization
Documentation
Deployment
```

---

# Final Architecture

```
                        USER
                          │
                          ▼
                   Next.js Frontend
                          │
                          ▼
                     FastAPI Backend
                          │
      ┌───────────────────┼────────────────────┐
      │                   │                    │
      ▼                   ▼                    ▼
 Search Service      AI Service         Prediction Service
      │                   │                    │
      │          ┌────────┴────────┐           │
      │          │                 │           │
      ▼          ▼                 ▼           ▼
 PostgreSQL   ChromaDB       Weather APIs   ML Model
      ▲
      │
 Event Pipeline
      ▲
      │
Normalize
Validate
Enrich
Deduplicate
      ▲
      │
IMD • CWC • Weather • RSS
```

---

# Milestone Definition

A milestone is complete only when it is independently testable.

* **Milestone 1:** Mock APIs return realistic data.
* **Milestone 2:** Data is normalized and stored correctly.
* **Milestone 3:** Users can search flood events by location.
* **Milestone 4:** AI summarizes live events.
* **Milestone 5:** RAG answers preparedness questions.
* **Milestone 6:** Hybrid AI combines live data with RAG.
* **Milestone 7:** Flood prediction and interactive dashboard are fully integrated.
