"""Fast, OCR-free ingestion of the flood guideline PDFs into Chroma.

Why this exists alongside ingest.py: the original pipeline runs `unstructured` in
hi_res mode with Tesseract OCR and a vision LLM captioning every chart, which is the
higher-quality path but needs system binaries and tens of minutes. This one pulls the
embedded text layer with PyMuPDF and embeds it with Chroma's bundled ONNX MiniLM —
no torch, no OCR, no API key, runs in a couple of minutes.

Tradeoff, stated plainly: text inside scanned pages and charts is NOT captured here.
For those documents, ingest.py remains the correct tool.

Run:  .venv/bin/python services/rag/fast_ingest.py
"""
import argparse
import re
import sys
from pathlib import Path

import chromadb
import fitz  # PyMuPDF

ROOT = Path(__file__).resolve().parents[2]
PDF_ROOT = ROOT / "data" / "rag"
CHROMA_DIR = ROOT / "services" / "rag" / "chroma_db"
COLLECTION = "flood_guidelines"

CHUNK_CHARS = 1200
CHUNK_OVERLAP = 200
MIN_CHUNK_CHARS = 120


def clean(text: str) -> str:
    text = text.replace("\xa0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def chunk_text(text: str) -> list[str]:
    """Paragraph-aware sliding window — keeps clauses intact where it can."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    buffer = ""

    for para in paragraphs:
        if len(buffer) + len(para) + 2 <= CHUNK_CHARS:
            buffer = f"{buffer}\n\n{para}" if buffer else para
            continue
        if buffer:
            chunks.append(buffer)
        if len(para) <= CHUNK_CHARS:
            buffer = para
        else:
            # A single oversized paragraph gets a hard sliding window.
            start = 0
            while start < len(para):
                chunks.append(para[start:start + CHUNK_CHARS])
                start += CHUNK_CHARS - CHUNK_OVERLAP
            buffer = ""
    if buffer:
        chunks.append(buffer)

    return [c for c in chunks if len(c) >= MIN_CHUNK_CHARS]


def extract(pdf_path: Path) -> list[dict]:
    doc = fitz.open(pdf_path)
    source_org = pdf_path.parent.name.replace("_", " ")
    title = pdf_path.stem.replace("_", " ")
    records: list[dict] = []

    for page_no, page in enumerate(doc, start=1):
        page_text = clean(page.get_text("text"))
        if len(page_text) < MIN_CHUNK_CHARS:
            continue   # cover pages / image-only pages — no text layer to embed
        for idx, chunk in enumerate(chunk_text(page_text)):
            records.append({
                "id": f"{pdf_path.stem}-p{page_no}-c{idx}",
                "document": chunk,
                "metadata": {
                    "source_file": pdf_path.name,
                    "source_org": source_org,
                    "title": title,
                    "page": page_no,
                },
            })
    doc.close()
    return records


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="drop the collection first")
    args = parser.parse_args()

    pdfs = sorted(PDF_ROOT.rglob("*.pdf"))
    if not pdfs:
        print(f"No PDFs found under {PDF_ROOT}")
        return 1

    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    if args.reset:
        try:
            client.delete_collection(COLLECTION)
            print(f"Dropped existing collection '{COLLECTION}'")
        except Exception:
            pass

    collection = client.get_or_create_collection(
        name=COLLECTION, metadata={"hnsw:space": "cosine"}
    )

    total = 0
    for pdf in pdfs:
        records = extract(pdf)
        if not records:
            print(f"  {pdf.name}: no extractable text layer — needs the OCR path in ingest.py")
            continue
        # Batch so a large document does not blow the embedding call.
        for i in range(0, len(records), 128):
            batch = records[i:i + 128]
            collection.upsert(
                ids=[r["id"] for r in batch],
                documents=[r["document"] for r in batch],
                metadatas=[r["metadata"] for r in batch],
            )
        total += len(records)
        print(f"  {pdf.name}: {len(records)} chunks")

    print(f"\nIndexed {total} chunks from {len(pdfs)} PDFs into {CHROMA_DIR}")
    print(f"Collection '{COLLECTION}' now holds {collection.count()} chunks")
    return 0


if __name__ == "__main__":
    sys.exit(main())
