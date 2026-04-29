from app.memory import add_turn, clear_session, get_history, replace_history
from app.main import app
from app.summarizer import summary_used, truncate_or_summarize
from fastapi.testclient import TestClient


client = TestClient(app)


def test_memory_round_trip():
    session_id = "unit-test-session"
    clear_session(session_id)
    add_turn(session_id, "user", "What is KYC?")
    add_turn(session_id, "assistant", "KYC verifies customer identity.")

    history = get_history(session_id)
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[1]["role"] == "assistant"


def test_truncate_or_summarize_creates_system_summary():
    session_id = "summary-session"
    clear_session(session_id)
    history = []
    for index in range(12):
        role = "user" if index % 2 == 0 else "assistant"
        history.append({"role": role, "content": f"turn-{index}"})

    summarized = truncate_or_summarize(history, llm=None)
    replace_history(session_id, summarized)

    assert summary_used(summarized) is True
    assert summarized[0]["role"] == "system"
    assert len(summarized) <= 5


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert "sessions" in payload


def test_chat_endpoint_with_memory(monkeypatch):
    clear_session("api-memory-session")

    monkeypatch.setattr(
        "app.main.get_rag_response",
        lambda question, history=None, backend=None: {
            "response": f"stubbed response for {question}",
            "sources": ["banking_knowledge.txt"],
            "confidence": "High",
            "history_used": bool(history),
            "backend": backend or "openai",
        },
    )

    response = client.post(
        "/chat",
        json={"message": "What is KYC?", "session_id": "api-memory-session", "use_memory": True},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["session_id"] == "api-memory-session"
    assert payload["sources"] == ["banking_knowledge.txt"]
    assert payload["turn_count"] == 2


def test_chat_compare_returns_both_backend_sections(monkeypatch):
    clear_session("compare-session")

    def fake_rag_response(question, history=None, backend=None):
        return {
            "response": f"{backend} response",
            "sources": ["shared_context.txt"],
            "confidence": "Moderate",
            "history_used": bool(history),
            "backend": backend,
        }

    monkeypatch.setattr("app.main.get_rag_response", fake_rag_response)

    response = client.post(
        "/chat/compare",
        json={"message": "Compare AML and KYC", "session_id": "compare-session", "use_memory": True},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["openai_response"]["backend"] == "openai"
    assert payload["hf_model_response"]["backend"] == "local_hf"
    assert payload["turn_count"] == 2


def test_chat_without_memory_keeps_turn_count_zero(monkeypatch):
    monkeypatch.setattr(
        "app.main.get_rag_response",
        lambda question, history=None, backend=None: {
            "response": "stateless answer",
            "sources": ["banking_knowledge.txt"],
            "confidence": "Moderate",
            "history_used": bool(history),
            "backend": backend or "openai",
        },
    )

    response = client.post(
        "/chat",
        json={"message": "What is AML?", "session_id": "stateless-session", "use_memory": False},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["turn_count"] == 0
    assert payload["history_used"] is False
