import asyncio
import uuid

from fastapi import FastAPI, HTTPException

from app.memory import add_turn, clear_session, get_history, replace_history
from app.models import BackendAnswer, ChatRequest, ChatResponse, CompareChatResponse, HealthResponse
from app.rag_chain import get_llm, get_rag_response
from app.summarizer import summary_used, truncate_or_summarize


app = FastAPI(
    title="Banking GenAI Conversational API",
    version="1.0.0",
    description="FastAPI backend that adds session-aware memory to the banking RAG assistant.",
)


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    from app.memory import _sessions  # local import to avoid exporting mutable state

    return HealthResponse(status="ok", sessions=len(_sessions))


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    session_id = request.session_id or str(uuid.uuid4())
    raw_history = get_history(session_id) if request.use_memory else []

    llm = None
    if request.use_memory and len(raw_history) > 10:
        try:
            llm = get_llm()
        except RuntimeError:
            llm = None

    memory_history = truncate_or_summarize(raw_history, llm) if request.use_memory else []
    if request.use_memory and memory_history != raw_history:
        replace_history(session_id, memory_history)

    try:
        result = get_rag_response(question=request.message, history=memory_history)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if request.use_memory:
        add_turn(session_id, "user", request.message)
        add_turn(session_id, "assistant", result["response"])

    return ChatResponse(
        session_id=session_id,
        response=result["response"],
        turn_count=len(get_history(session_id)) if request.use_memory else 0,
        sources=result["sources"],
        confidence=result["confidence"],
        history_used=result["history_used"],
        summary_used=summary_used(memory_history),
    )


@app.post("/chat/compare", response_model=CompareChatResponse)
async def compare_backends(request: ChatRequest) -> CompareChatResponse:
    session_id = request.session_id or str(uuid.uuid4())
    raw_history = get_history(session_id) if request.use_memory else []

    llm = None
    if request.use_memory and len(raw_history) > 10:
        try:
            llm = get_llm("openai")
        except RuntimeError:
            llm = None

    memory_history = truncate_or_summarize(raw_history, llm) if request.use_memory else []
    if request.use_memory and memory_history != raw_history:
        replace_history(session_id, memory_history)

    async def run_backend(name: str):
        return await asyncio.to_thread(
            get_rag_response,
            request.message,
            memory_history,
            name,
        )

    try:
        openai_result, hf_result = await asyncio.gather(
            run_backend("openai"),
            run_backend("local_hf"),
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if request.use_memory:
        add_turn(session_id, "user", request.message)
        add_turn(session_id, "assistant", openai_result["response"])

    return CompareChatResponse(
        session_id=session_id,
        question=request.message,
        openai_response=BackendAnswer(
            backend=openai_result["backend"],
            response=openai_result["response"],
            sources=openai_result["sources"],
            confidence=openai_result["confidence"],
            history_used=openai_result["history_used"],
        ),
        hf_model_response=BackendAnswer(
            backend=hf_result["backend"],
            response=hf_result["response"],
            sources=hf_result["sources"],
            confidence=hf_result["confidence"],
            history_used=hf_result["history_used"],
        ),
        turn_count=len(get_history(session_id)) if request.use_memory else 0,
        summary_used=summary_used(memory_history),
    )


@app.delete("/session/{session_id}")
async def clear(session_id: str) -> dict[str, str]:
    clear_session(session_id)
    return {"status": "cleared"}
