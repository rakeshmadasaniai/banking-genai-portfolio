from typing import Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User message for the assistant.")
    session_id: Optional[str] = Field(default=None, description="Existing session identifier for multi-turn memory.")
    use_memory: bool = Field(default=True, description="When false, bypass conversational memory for the request.")


class ChatResponse(BaseModel):
    session_id: str
    response: str
    turn_count: int
    sources: list[str]
    confidence: str
    history_used: bool
    summary_used: bool


class BackendAnswer(BaseModel):
    backend: str
    response: str
    sources: list[str]
    confidence: str
    history_used: bool


class CompareChatResponse(BaseModel):
    session_id: str
    question: str
    openai_response: BackendAnswer
    hf_model_response: BackendAnswer
    turn_count: int
    summary_used: bool


class HealthResponse(BaseModel):
    status: str
    sessions: int
