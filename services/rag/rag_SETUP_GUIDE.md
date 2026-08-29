# FloodGuard RAG — Running Locally

This guide is for team members who have already cloned the repo. All scripts and config files are included.

> **The vector database (`chroma_db`) is shared separately via Google Drive** since it is too large for GitHub (296 MB). You do **not** need to run `ingest.py` yourself.

---

## Prerequisites

> **These are only required if you need to re-run `ingest.py`** (e.g. documents were updated). If you are just running the chat app (`app.py`), skip straight to Step 1.

### Poppler (PDF rendering)

1. Download the latest Windows release from [github.com/oschwartz10612/poppler-windows/releases](https://github.com/oschwartz10612/poppler-windows/releases)
2. Extract it anywhere (e.g. `C:\Program Files\poppler-26.02.0\`)
3. Add the `\Library\bin` subfolder to your **User PATH**:
   - Search "Environment Variables" in the Start menu
   - Under **User variables**, select `Path` ? **Edit** ? **New**
   - Paste: `C:\Program Files\poppler-26.02.0\Library\bin`
4. Restart your terminal

### Tesseract-OCR

1. Download the installer from [github.com/UB-Mannheim/tesseract/wiki](https://github.com/UB-Mannheim/tesseract/wiki)
2. Run it (default install path: `C:\Program Files\Tesseract-OCR`)
3. Restart your terminal

---

## Step 1: Download the Vector Database

The `chroma_db/` folder contains the pre-built vector embeddings of all flood management documents. Download and extract it from the shared Google Drive link:

> **[Download chroma_db.zip — Google Drive](#)**
> *(Replace this placeholder with the actual Drive link)*

After downloading, extract the zip so the folder structure looks like this:

```
FloodGuard/
+-- rag/
    +-- chroma_db/       <- place it here
        +-- chroma.sqlite3
        +-- ...
```

---

## Step 2: Get an OpenRouter API Key

The app uses a **free** LLM via [openrouter.ai](https://openrouter.ai):

1. Sign up at [openrouter.ai](https://openrouter.ai)
2. Go to **Keys** ? **Create Key**
3. Copy the key (starts with `sk-or-v1-...`)

---

## Step 3: Create the `.env` file

Inside the `rag/` folder, create a file called `.env` with this content:

```
OPENAI_API_KEY=sk-or-v1-your-key-here
```

> The `.env` file is gitignored and will never be committed to the repo. Every team member needs their own key.

---

## Step 4: Set Up the Python Environment

Open a terminal inside `FloodGuard\rag\`:

```cmd
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

> This installs all dependencies including `torch`, `unstructured`, `chromadb`, and `langchain`. It may take **5-10 minutes** on first run.

---

## Step 5: Run the Chat App

```cmd
venv\Scripts\python.exe app.py
```

Type your question and hit Enter:

```
RAG System Ready! Type 'exit' or 'quit' to stop.

Ask a question about the Flood Guidelines: what is the role of NDMA?

Searching documents...
Generating answer...
--------------------------------------------------
The NDMA (National Disaster Management Authority) is responsible for...
--------------------------------------------------
```

---

## When Documents Are Updated

When the team lead updates the PDF documents and re-runs ingestion, they will upload a new `chroma_db.zip` to Drive. You just need to:

1. Delete your existing `rag/chroma_db/` folder
2. Download the new zip from Drive
3. Extract it to `rag/chroma_db/`
4. Run `app.py` — it will immediately use the updated database

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `Vector database not found` error | Make sure you extracted `chroma_db/` into `rag/chroma_db/` (not a nested folder inside it) |
| `TesseractNotFoundError` | Only relevant if running `ingest.py` — restart terminal after installing Tesseract |
| `ModuleNotFoundError` for any package | Run `pip install -r requirements.txt` again |
| `404 Model not found` on OpenRouter | The free model was retired — update the `model=` string in `app.py` to another active free model from [openrouter.ai/models](https://openrouter.ai/models) |
| Slow first startup | Normal — the HuggingFace embedding model is loading from disk into RAM on first run |
