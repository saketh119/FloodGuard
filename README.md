# 🌊 FloodGuard

> **An AI-Powered Real-Time Flood Response and Alert System**

FloodGuard is an AI-powered disaster management platform that predicts flood risk using Machine Learning, provides real-time weather updates, recommends nearby shelters, and assists users through a Retrieval-Augmented Generation (RAG) based AI assistant built on trusted government guidelines.

---

# ✨ Features

- 🌊 Flood Risk Prediction
- 🤖 AI Assistant (RAG)
- 🌦️ Real-Time Weather Updates
- 🗺️ Interactive Flood Map
- 🏠 Shelter Recommendation
- 🚨 Emergency Alerts
- 📍 Nearby Safe Shelter Navigation

---

# 🏗️ Target System Architecture

```mermaid
flowchart TD
    U[Users]

    U --> F[Next.js Frontend]

    F --> G[FastAPI API Gateway]

    G --> P[Flood Prediction Service]
    G --> A[AI Assistant (RAG)]
    G --> L[Live Updates Service]
    G --> S[Shelter Service]

    P --> DB[(Supabase)]
    A --> DB
    L --> DB
    S --> DB

    DB --> PG[(PostgreSQL + pgvector)]

    W[Weather APIs] --> L
    GOV[Government Data] --> L
    DOC[RAG Documents] --> A
```

---

# 🛠️ Technology Stack

| Layer | Technology |
|--------|------------|
| Frontend | Next.js, TypeScript, Tailwind CSS |
| Backend | FastAPI |
| Database | Supabase (PostgreSQL + pgvector) |
| Machine Learning | Scikit-learn, XGBoost |
| AI | LangChain, Google Gemini |
| Maps | Leaflet, OpenStreetMap |
| Deployment | Docker, Vercel, Render |

---

# 📂 Project Structure

```text
FloodGuard/
│
├── backend/                  # FastAPI backend
│
├── frontend/                 # Next.js frontend
│
├── ml/
│   ├── notebooks/
│   ├── preprocessing/
│   ├── training/
│   └── models/
│
├── datasets/
│   ├── raw/
│   │   ├── ml/
│   │   └── rag/
│   └── processed/
│
├── docs/                     # Project documentation
│
├── deployment/               # Docker & deployment files
│
├── scripts/                  # Utility scripts
│
├── README.md
│
└── docker-compose.yml
```

---

# 📊 Dataset Sources

### Machine Learning

- Flood Risk Dataset (India)
- Indian Rainfall Dataset (District-wise)
- INDOFLOODS Dataset
- Catchment Characteristics
- Precipitation Variables

### RAG Knowledge Base

- National Disaster Management Authority (NDMA)
- India Meteorological Department (IMD)
- National Disaster Response Force (NDRF)
- National Disaster Management Plan (NDMP)

---

# 🚀 Current Status

- ✅ Project Planning
- ✅ Dataset Collection
- ✅ RAG Document Collection
- ✅ Repository Setup
- ⏳ Data Exploration
- ⏳ Data Preprocessing
- ⏳ Model Training
- ⏳ Backend Development
- ⏳ RAG Integration
- ⏳ Frontend Development
- ⏳ Deployment

---

# 📄 License

This project is developed for academic and research purposes.
