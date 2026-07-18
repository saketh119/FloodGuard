# FloodGuard RAG — Running Locally

This guide is for team members who have already cloned the repo. All scripts and config files are included. You just need to set up your environment and run the two scripts.

---

## Prerequisites

Install these two system-level tools before anything else. They are **not** Python packages and must be installed manually.

### 1. Poppler (PDF rendering)

1. Download the latest Windows release from [github.com/oschwartz10612/poppler-windows/releases](https://github.com/oschwartz10612/poppler-windows/releases)
2. Extract it anywhere (e.g. `C:\Program Files\poppler-26.02.0\`)
3. Add the `\Library\bin` subfolder to your **User PATH**:
   - Search "Environment Variables" in the Start menu
   - Under **User variables**, select `Path` → **Edit** → **New**
   - Paste: `C:\Program Files\poppler-26.02.0\Library\bin`
4. Restart your terminal

### 2. Tesseract-OCR

1. Download the installer from [github.com/UB-Mannheim/tesseract/wiki](https://github.com/UB-Mannheim/tesseract/wiki)
2. Run it (default install path: `C:\Program Files\Tesseract-OCR`)
3. Restart your terminal

> **Note:** The `ingest.py` script already injects the Tesseract path at runtime, so even if you forget to add it to PATH it will still work.

---

## Step 1: Get an OpenRouter API Key

The app uses a **free** LLM via [openrouter.ai](https://openrouter.ai):

1. Sign up at [openrouter.ai](https://openrouter.ai)
2. Go to **Keys** → **Create Key**
3. Copy the key (starts with `sk-or-v1-...`)

---

## Step 2: Create the `.env` file

Inside the `rag/` folder, create a file called `.env` with this content:

```env
OPENAI_API_KEY=sk-or-v1-your-key-here
```

> The `.env` file is gitignored and will never be committed to the repo. Every team member needs their own key.

---

## Step 3: Set Up the Python Environment

Open a terminal inside `D:\FloodGuard\rag\` (or wherever you cloned it):

```cmd
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

> This installs all dependencies including `torch`, `unstructured`, `chromadb`, and `langchain`. It may take **5–10 minutes** on first run.

---

## Step 4: Run Ingestion (One-Time Only)

This reads all PDFs in `datasets/rag/`, chunks them, generates embeddings, and saves the vector database locally.

```cmd
venv\Scripts\python.exe ingest.py
```

**This only needs to be done once.** The resulting `chroma_db/` folder is gitignored, so each team member must run this locally. Expect it to take **30 minutes to 2 hours** depending on CPU speed (it runs OCR on every page).

You'll see output like this when it's done:
```
Ingestion complete. ChromaDB saved to ...\chroma_db
```

---

## Step 5: Run the Chat App

Once ingestion is done, launch the interactive CLI:

```cmd
venv\Scripts\python.exe app.py
```

Type your question and hit Enter:
```
RAG System Ready! Type 'exit' or 'quit' to stop.

Ask a question about the Flood Guidelines: what is the role of NDMA?
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `TesseractNotFoundError` | Restart your terminal after installing Tesseract |
| `ModuleNotFoundError` for any package | Run `pip install -r requirements.txt` again |
| `404 Model not found` on OpenRouter | The free model was retired — update the `model=` string in `app.py` to another active free model from [openrouter.ai/models](https://openrouter.ai/models) |
| `FileNotFoundError` on a PDF during ingestion | Run `ingest.py` again; a file was deleted while it was running |
