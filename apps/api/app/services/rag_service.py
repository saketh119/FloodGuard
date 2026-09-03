"""RAG service — retrieve from Chroma, then ground a Gemini answer in what came back.

Without a Gemini key this still answers, extractively: the retrieved passages are
returned verbatim with their citations. Retrieval is the part that must always work.
"""
import re
from functools import lru_cache
from typing import Any

import chromadb

from app.core.config import settings
from app.core.logger import get_logger
from app.services.llm import LLMUnavailable, generate

log = get_logger("floodguard.rag")

SYSTEM_PROMPT = (
    "You are the FloodGuard assistant for Indian flood preparedness and response. "
    "Answer ONLY from the provided context, which is drawn from official NDMA, IMD and "
    "NDRF publications. Cite the source document and page inline as [Title, p.N] after "
    "each claim. If the context does not contain the answer, say so plainly and suggest "
    "which kind of official document would carry it. Never invent phone numbers, "
    "thresholds, or procedures. Be concise and use short bullets for procedures."
)


@lru_cache(maxsize=1)
def _collection():
    """Chroma client is expensive to build; one per process."""
    if not settings.CHROMA_DIR.exists():
        raise FileNotFoundError(
            f"Vector store missing at {settings.CHROMA_DIR}. Run: .venv/bin/python services/rag/fast_ingest.py"
        )
    client = chromadb.PersistentClient(path=str(settings.CHROMA_DIR))
    return client.get_collection(settings.CHROMA_COLLECTION)


def index_status() -> dict[str, Any]:
    try:
        col = _collection()
        return {"available": True, "collection": settings.CHROMA_COLLECTION, "chunks": col.count()}
    except Exception as exc:
        return {"available": False, "error": str(exc), "chunks": 0}


# Government PDFs repeat headers, footers and disclaimers on every page. Those chunks
# are near-identical, so a single boilerplate line can occupy the entire top-k and
# push the passage that actually answers the question off the end.
OVERFETCH = 4          # pull k*4 candidates, then filter down to k
MAX_PER_DOCUMENT = 2   # no single PDF may dominate the context
_FINGERPRINT_CHARS = 160

# Hybrid retrieval. Pure vector search misses passages that name the exact term the
# user asked about — "Orange warning" sits in a criteria table whose surrounding
# language looks nothing like the question, so MiniLM ranks it below boilerplate that
# merely sounds topical. A keyword pass over the same collection recovers those.
KEYWORD_BONUS = 0.12   # added to a passage's score per distinct query term it contains
MAX_KEYWORD_TERMS = 4

_STOPWORDS = {
    "what", "does", "mean", "the", "and", "for", "are", "with", "that", "this", "from",
    "should", "would", "how", "why", "when", "who", "which", "into", "about", "there",
    "their", "them", "they", "have", "has", "been", "will", "can", "could", "must",
    "during", "after", "before", "please", "tell", "explain", "describe", "give",
    "officials", "official", "take", "any", "all", "its", "was", "were",
}


def _fingerprint(text: str) -> str:
    """Normalised prefix — catches the same boilerplate reprinted on many pages."""
    return " ".join(text.split()).lower()[:_FINGERPRINT_CHARS]


def _salient_terms(question: str) -> list[str]:
    """The words worth matching literally, longest first."""
    words = re.findall(r"[a-zA-Z]{4,}", question.lower())
    seen, terms = set(), []
    for w in sorted(set(words), key=len, reverse=True):
        if w in _STOPWORDS or w in seen:
            continue
        seen.add(w)
        terms.append(w)
    return terms[:MAX_KEYWORD_TERMS]


def _candidates(col, question: str, k: int) -> list[dict[str, Any]]:
    """Vector hits plus keyword hits, merged and scored."""
    pool: dict[str, dict[str, Any]] = {}

    def add(doc, meta, distance, source):
        key = _fingerprint(doc)
        similarity = (1 - distance) if distance is not None else 0.5
        entry = pool.get(key)
        if entry is None:
            pool[key] = {"text": doc, "meta": meta or {}, "similarity": similarity,
                         "score": similarity, "sources": {source}}
        else:
            entry["similarity"] = max(entry["similarity"], similarity)
            entry["sources"].add(source)

    res = col.query(query_texts=[question], n_results=k * OVERFETCH)
    for doc, meta, dist in zip((res.get("documents") or [[]])[0],
                               (res.get("metadatas") or [[]])[0],
                               (res.get("distances") or [[]])[0]):
        add(doc, meta, dist, "vector")

    # Keyword pass — one filtered query per salient term.
    for term in _salient_terms(question):
        try:
            hit = col.query(query_texts=[question], n_results=k,
                            where_document={"$contains": term})
        except Exception as exc:                     # filter unsupported / no match
            log.debug("keyword pass for %r failed: %s", term, exc)
            continue
        for doc, meta, dist in zip((hit.get("documents") or [[]])[0],
                                   (hit.get("metadatas") or [[]])[0],
                                   (hit.get("distances") or [[]])[0]):
            add(doc, meta, dist, f"kw:{term}")

    # Final score: semantic similarity, lifted for each distinct query term present.
    for entry in pool.values():
        matched = sum(1 for s in entry["sources"] if s.startswith("kw:"))
        entry["score"] = entry["similarity"] + KEYWORD_BONUS * matched
        entry["matched_terms"] = matched

    return sorted(pool.values(), key=lambda e: e["score"], reverse=True)


def retrieve(question: str, k: int | None = None) -> list[dict[str, Any]]:
    k = k or settings.RAG_TOP_K
    col = _collection()
    ranked = _candidates(col, question, k)

    passages: list[dict[str, Any]] = []
    per_document: dict[str, int] = {}

    def take(entry: dict[str, Any]) -> None:
        meta = entry["meta"]
        passages.append({
            "rank": len(passages) + 1,
            "text": entry["text"],
            "title": meta.get("title", "Unknown document"),
            "page": meta.get("page"),
            "source_file": meta.get("source_file"),
            "source_org": meta.get("source_org"),
            "relevance": round(entry["similarity"], 3),
            "matched_terms": entry.get("matched_terms", 0),
        })

    # First pass honours the per-document cap so one PDF cannot fill the context.
    for entry in ranked:
        if len(passages) >= k:
            break
        source = entry["meta"].get("source_file", "?")
        if per_document.get(source, 0) >= MAX_PER_DOCUMENT:
            continue
        per_document[source] = per_document.get(source, 0) + 1
        take(entry)

    # If the cap starved the result, top up rather than answer from too little.
    if len(passages) < k:
        chosen = {p["text"] for p in passages}
        for entry in ranked:
            if len(passages) >= k:
                break
            if entry["text"] not in chosen:
                take(entry)

    return passages


def _context_block(passages: list[dict]) -> str:
    return "\n\n---\n\n".join(
        f"[{p['title']}, p.{p['page']}]\n{p['text']}" for p in passages
    )


def _extractive_answer(question: str, passages: list[dict], exc=None) -> str:
    """No-LLM fallback: hand back the sources, clearly labelled as unsynthesised."""
    if not passages:
        return "No relevant passage was found in the indexed NDMA/IMD guidelines for that question."

    if exc is None or getattr(exc, "reason", "no_key") == "no_key":
        note = ("_No Gemini key is configured, so these are the most relevant passages "
                "from the official guidelines, returned verbatim rather than summarised._")
    else:
        note = (f"_Gemini could not answer ({exc}), so these are the most relevant "
                f"passages from the official guidelines, returned verbatim._")
    lines = [note + "\n"]
    for p in passages:
        snippet = p["text"][:600].rstrip()
        lines.append(f"**{p['title']}, p.{p['page']}**\n{snippet}…\n")
    return "\n".join(lines)


# Openers that are not document questions. Running retrieval on these returns
# whichever passage happens to be least dissimilar to "hi", which reads as broken.
_GREETINGS = {
    "hi", "hii", "hey", "hello", "helo", "yo", "hiya", "namaste", "good morning",
    "good afternoon", "good evening", "greetings", "sup", "hola", "thanks",
    "thank you", "ty", "ok", "okay", "cool", "bye", "test", "testing",
}

_CAPABILITIES = (
    "Hello. I answer questions about Indian flood preparedness and response from "
    "official NDMA, IMD and NDRF publications, and I cite the document and page "
    "behind every answer.\n\n"
    "You could ask me:\n"
    "- What does an Orange colour code warning mean for heavy rainfall?\n"
    "- What are the NDMA guidelines for urban flood management?\n"
    "- How should a district prepare an evacuation plan?\n"
    "- What does flood plain zoning require?"
)


def _is_conversational(question: str) -> bool:
    """True for greetings and pleasantries, which deserve a reply, not a search."""
    cleaned = re.sub(r"[^a-z\s]", "", question.lower()).strip()
    return bool(cleaned) and (cleaned in _GREETINGS or len(cleaned) < 3)


async def answer(question: str, k: int | None = None) -> dict[str, Any]:
    if _is_conversational(question):
        return {"answer": _CAPABILITIES, "citations": [], "grounded": False,
                "llm_used": False, "conversational": True}

    passages = retrieve(question, k)

    citations = [
        {"title": p["title"], "page": p["page"], "source_org": p["source_org"],
         "source_file": p["source_file"], "relevance": p["relevance"]}
        for p in passages
    ]

    if not passages:
        return {"answer": "Nothing in the indexed guidelines covers that question.",
                "citations": [], "grounded": False, "llm_used": False}

    try:
        text = await generate(
            prompt=f"Context:\n{_context_block(passages)}\n\nQuestion: {question}\n\nAnswer:",
            system=SYSTEM_PROMPT,
        )
        return {"answer": text, "citations": citations, "grounded": True, "llm_used": True}
    except LLMUnavailable as exc:
        # A configured-but-failing key must be visible, not silently swallowed.
        level = log.info if exc.reason == "no_key" else log.warning
        level("Falling back to extractive answer: %s", exc)
        return {"answer": _extractive_answer(question, passages, exc), "citations": citations,
                "grounded": True, "llm_used": False,
                "llm_error": str(exc), "llm_error_reason": exc.reason}
