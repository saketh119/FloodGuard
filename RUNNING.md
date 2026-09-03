# Running FloodGuard

Three processes. `make help` lists every task.

```
apps/mock-imd  :8080   stands in for the real IMD API
      ↓
apps/api       :8000   FastAPI gateway — ingests, correlates, scores, answers
      ↓
apps/web       :3000   Next.js dashboard — talks only to the gateway
```

## One-time setup

```bash
make setup      # venv + Python deps + npm install
make train      # flood-severity model → services/ml/models/
make ingest     # RAG vector store → services/rag/chroma_db/  (~2 min, 80MB ONNX download)
```

## API keys

**Two keys, both optional.** Everything runs without either — features degrade visibly rather than silently.

| What | Key needed? | Notes |
|---|---|---|
| **Gemini** (chat answers, AI summaries) | `GEMINI_API_KEY` | Free at [aistudio.google.com/apikey](https://aistudio.google.com/apikey). Optional — see below. |
| **OpenWeather** (live conditions + forecast) | `OPENWEATHER_API_KEY` | Free at [openweathermap.org/api](https://openweathermap.org/api). 14 calls per cycle, well inside the 60/min free limit. Optional — without it the platform runs on IMD alone. |
| **IMD** (warnings, district rainfall) | none | Served by `apps/mock-imd`. The real IMD API needs government credentials; when you get them, change `IMD_BASE_URL`. |
| **Embeddings** | none | Chroma's bundled ONNX MiniLM runs locally. |
| **ML model** | none | A local `.joblib` file you train yourself. |
| **Database** | none | SQLite file. |

Paste your key into `apps/api/.env` (already created for you, blank and gitignored):

```bash
GEMINI_API_KEY=AIza...
```

Then confirm it actually works:

```bash
python run.py doctor
```

which makes a real Gemini call and tells you exactly what went wrong if it fails —
bad key, wrong model name, or quota exhausted.

### Without a key

Everything still runs. `/chat` returns the retrieved guideline passages verbatim
instead of a written answer, and event summaries use a deterministic template. Both
label themselves in the UI, so you always know which path produced the text.

A key that is *set but failing* is treated as an error, not as "no key" — the chat
page shows a red banner naming the cause. A silent downgrade would be worse than a
visible failure.

## Run

One command, one terminal:

```bash
python run.py
```

That starts all three, waits until each is answering, and prints the URL.
Ctrl+C stops everything. Output is tagged per service so one terminal stays readable.

```
  ▸ mock  starting on :8080
  ▸ api   starting on :8000
  ▸ web   starting on :3000

  ✓ mock  http://localhost:8080
  ✓ api   http://localhost:8000
  ✓ web   http://localhost:3000

  Open http://localhost:3000
```

Other forms:

```bash
python run.py api      # just one service — mock | api | web
python run.py check    # are they up?
python run.py doctor   # diagnose setup and verify the Gemini key works
```

`run.py` checks before it starts: virtualenv present, `npm install` done, model
trained, vector store built, ports free — and prints the fix for whatever is missing
instead of failing halfway through startup.

To force a collection cycle instead of waiting 60s for the scheduler:

```bash
curl -X POST http://localhost:8000/ingest/run
```

## How the frontend reaches the backend

The browser only ever calls **same-origin `/api/*`**. `apps/web/next.config.mjs`
rewrites that to the gateway, so:

- the API hostname never ships in the client bundle,
- there is no CORS negotiation in the browser,
- deploying means changing one variable, `FLOODGUARD_API_BASE`.

The web app has exactly one upstream. It does not call IMD.

## Endpoints

| Endpoint | What it does |
|---|---|
| `GET /health` | Which subsystems are live — DB counts, model, RAG index, LLM key |
| `GET /districts` | Location registry backing the picker |
| `GET /dashboard/{district}` | Everything one district view needs, in one round trip |
| `GET /events` | Correlated flood events; filter by district/state/status/severity/min_risk |
| `GET /events/{id}` | One event plus its full evidence trail |
| `POST /events/{id}/summary` | Regenerate that event's AI narrative |
| `GET /stations` | Station registry with coordinates |
| `GET /observations` | The immutable raw IMD feed, for auditing |
| `GET /predictions` | Stored scoring history |
| `POST /predictions/run` | Re-score every open event now |
| `GET /predictions/model` | Model provenance and its cross-validated score |
| `POST /chat` | Grounded Q&A over NDMA/IMD/NDRF guidelines, with citations |
| `POST /ingest/run` | Run one full pipeline pass |

## Environment

`apps/api/.env`:

| Variable | Default | Purpose |
|---|---|---|
| `GEMINI_API_KEY` | *(empty)* | Enables generated answers and AI summaries |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Which Gemini model to call |
| `IMD_BASE_URL` | `http://localhost:8080` | Swap for the real IMD API when credentials land |
| `COLLECT_INTERVAL_S` | `60` | Scheduler period |
| `SCHEDULER_ENABLED` | `true` | `false` to collect only on demand |
| `CORRELATION_WINDOW_HOURS` | `6` | How long an event stays open to new evidence |

`apps/web/.env.local`:

| Variable | Default | Purpose |
|---|---|---|
| `FLOODGUARD_API_BASE` | `http://localhost:8000` | Rewrite target; server-side only |

## Running the services individually

`run.py` wraps these — reach for them only when you want a service in its own terminal.

```bash
# mock IMD
.venv/bin/python -m uvicorn mock_imd_server:app --port 8080 --app-dir apps/mock-imd --reload

# backend
cd apps/api && ../../.venv/bin/python -m uvicorn app.main:app --port 8000 --reload

# frontend
cd apps/web && npm run dev
```

`make mock` / `make api` / `make web` are the same thing, shorter.

Don't run `npm run build` while the web dev server is up — they contend over `.next`
and it kills the dev server.
