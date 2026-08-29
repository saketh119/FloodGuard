from fastapi import APIRouter, HTTPException

from app.schemas import ChatRequest, ChatResponse
from app.services import rag_service

router = APIRouter(tags=["ai"])


@router.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest):
    """Grounded Q&A over the NDMA/IMD/NDRF guideline corpus."""
    try:
        result = await rag_service.answer(payload.question, payload.top_k)
    except FileNotFoundError as exc:
        raise HTTPException(503, str(exc))
    return result


@router.get("/chat/status")
def chat_status():
    from app.services import llm
    return {"rag": rag_service.index_status(), "llm": llm.status()}


@router.get("/llm/check")
async def llm_check():
    """Make one real Gemini call and report exactly what happened.

    Without this a mistyped key is indistinguishable from no key: both silently fall
    back to extractive answers. `python run.py doctor` calls this.
    """
    from app.services import llm
    return await llm.probe()
