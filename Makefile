# FloodGuard — common tasks.
# `make help` lists everything.

VENV := .venv
PY   := $(VENV)/bin/python
PIP  := $(VENV)/bin/pip

.PHONY: help setup api web mock train ingest dev-check clean

help:
	@echo "FloodGuard"
	@echo "  make setup    Create the venv, install Python + Node dependencies"
	@echo "  make train    Train the flood-severity model into services/ml/models"
	@echo "  make ingest   Build the RAG vector store into services/rag/chroma_db"
	@echo ""
	@echo "  make mock     Run the mock IMD source      :8080"
	@echo "  make api      Run the FastAPI gateway      :8000"
	@echo "  make web      Run the Next.js dashboard    :3000"
	@echo ""
	@echo "  make dev-check  Verify all three services respond"

setup:
	python3.11 -m venv $(VENV)
	$(PIP) install -q --upgrade pip
	$(PIP) install -q -r apps/api/requirements.txt
	cd apps/web && npm install
	@echo "Setup complete. Next: make train && make ingest"

train:
	$(PY) services/ml/training/train_flood_severity.py

ingest:
	$(PY) services/rag/fast_ingest.py --reset

mock:
	$(PY) -m uvicorn mock_imd_server:app --port 8080 --app-dir apps/mock-imd --reload

api:
	cd apps/api && ../../$(VENV)/bin/python -m uvicorn app.main:app --port 8000 --reload

web:
	cd apps/web && npm run dev

dev-check:
	@printf "mock-imd :8080  "; curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8080/
	@printf "api      :8000  "; curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8000/health
	@printf "web      :3000  "; curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:3000/
	@printf "proxy    /api   "; curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:3000/api/health

clean:
	rm -f apps/api/floodguard.db
	rm -rf apps/web/.next
