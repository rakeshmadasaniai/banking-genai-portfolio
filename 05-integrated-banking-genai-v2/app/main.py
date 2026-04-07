import asyncio
import uuid

from fastapi import FastAPI, HTTPException

from app.config import APP_TITLE, APP_VERSION, LLM_BACKEND
from app.memory import add_turn, clear_session, get_history, replace_history, session_count
from app.models import BackendAnswer, ChatRequest, ChatResponse, CompareChatResponse, HealthResponse
from app.rag_chain import generate_with_shared_retrieval
from app.summarizer import summary_used, truncate_or_summarize


app = FastAPI(
    title=APP_TITLE,
    version=APP_VERSION,
    description="Version B integrated banking GenAI backend with shared retrieval, memory, and compare mode.",
)


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok", sessions=session_count(), backend_default=LLM_BACKEND)


def prepare_history(session_id: str, use_memory: bool) -> tuple[list[dict[str, str]], bool]:
    raw_history = get_history(session_id) if use_memory else []
    memory_history = truncate_or_summarize(raw_history, llm=None) if use_memory else []
    summarized = memory_history != raw_history
    if use_memory and summarized:
        replace_history(session_id, memory_history)
    return memory_history, summarized


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    session_id = request.session_id or str(uuid.uuid4())
    memory_history, _ = prepare_history(session_id, request.use_memory)

    try:
        result = generate_with_shared_retrieval(
            question=request.message,
            history=memory_history,
            backend_name=LLM_BACKEND,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if request.use_memory:
        add_turn(session_id, "user", request.message)
        add_turn(session_id, "assistant", result["response"])

    return ChatResponse(
        session_id=session_id,
        response=result["response"],
        backend_used=result["backend"],
        turn_count=len(get_history(session_id)) if request.use_memory else 0,
        sources=result["sources"],
        confidence=result["confidence"],
        history_used=result["history_used"],
        summary_used=summary_used(memory_history),
    )


@app.post("/chat/compare", response_model=CompareChatResponse)
async def compare(request: ChatRequest) -> CompareChatResponse:
    session_id = request.session_id or str(uuid.uuid4())
    memory_history, _ = prepare_history(session_id, request.use_memory)

    async def run_backend(name: str):
        return await asyncio.to_thread(
            generate_with_shared_retrieval,
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
        openai_response=BackendAnswer(**{k: openai_result[k] for k in ("backend", "response", "sources", "confidence", "history_used")}),
        hf_model_response=BackendAnswer(**{k: hf_result[k] for k in ("backend", "response", "sources", "confidence", "history_used")}),
        turn_count=len(get_history(session_id)) if request.use_memory else 0,
        summary_used=summary_used(memory_history),
    )


@app.delete("/session/{session_id}")
async def delete_session(session_id: str) -> dict[str, str]:
    clear_session(session_id)
    return {"status": "cleared"}
