# Repository Layout

```
FloodGuard/
├── apps/                        Independently runnable processes
│   ├── api/                     FastAPI gateway — the only service that talks to IMD
│   │   ├── app/
│   │   │   ├── core/            config, database engine, logging
│   │   │   ├── models/          SQLAlchemy tables
│   │   │   ├── schemas/         Pydantic request/response contracts
│   │   │   ├── flood/
│   │   │   │   ├── adapters/    per-source normalisation (IMD today, CWC/RSS next)
│   │   │   │   ├── collectors/  fetch + dedupe-insert
│   │   │   │   ├── engine/      trigger detection, event correlation
│   │   │   │   ├── geo.py       district registry / enrichment
│   │   │   │   ├── pipeline.py  one end-to-end cycle
│   │   │   │   └── scheduler.py APScheduler wiring
│   │   │   ├── services/        ML scoring, RAG, Gemini, summarisation
│   │   │   ├── routes/          HTTP surface
│   │   │   └── main.py
│   │   └── requirements.txt
│   ├── web/                     Next.js 15 App Router dashboard
│   │   └── src/
│   │       ├── app/             routes + root layout (one folder per page)
│   │       ├── features/        the nine page components
│   │       ├── components/      shared UI
│   │       ├── context/         FloodGuardContext — selected district + live data
│   │       ├── hooks/
│   │       └── lib/             api client, derive layer
│   └── mock-imd/                stand-in for the real IMD API until access lands
│
├── services/                    Pipelines and artifacts the API consumes
│   ├── ml/
│   │   ├── training/            training scripts
│   │   ├── models/              trained artifacts + metrics JSON
│   │   └── notebooks/           exploration
│   └── rag/
│       ├── fast_ingest.py       OCR-free ingestion (the one in use)
│       ├── ingest.py            hi-res OCR + vision ingestion (higher quality, slower)
│       ├── app.py               original CLI query tool
│       └── chroma_db/           vector store (gitignored — rebuild with fast_ingest)
│
├── data/                        raw + processed datasets, source PDFs
├── docs/                        architecture, plan, status, this file
├── deploy/                      deployment manifests
└── archive/                     superseded frontends, kept for reference
    ├── legacy-vite-dashboard/   React+Vite app the Next.js port came from
    └── legacy-html-prototype/   original static design mockup
```

## Why it is arranged this way

**`apps/` vs `services/`.** Anything in `apps/` is a process you start; anything in
`services/` is a pipeline that produces artifacts the API loads. Previously `backend/`,
`dashboard/`, `ml/` and `rag/` sat side by side at the root with no signal about which
were deployable.

**One frontend.** There used to be three: an empty `frontend/` placeholder, a static
`frontend_dashboard/` mockup, and the real `dashboard/`. The Next.js app is now the
only one, and the other two are in `archive/` rather than deleted.

**Docs are not at the root.** Six markdown files were competing with the code for
attention, one of them named `# Flood Intelligence Platform – End-to-E.md` — a literal
`#` and a truncated title that made it awkward to open from a shell.

**Data flows one way.** `apps/mock-imd` → `apps/api` → `apps/web`. The web app has one
upstream and never reaches past the gateway.
