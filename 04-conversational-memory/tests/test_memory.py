from app.memory import add_turn, clear_session, get_history, replace_history
from app.summarizer import summary_used, truncate_or_summarize


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
