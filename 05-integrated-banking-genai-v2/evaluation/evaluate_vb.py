import csv
import time
from pathlib import Path

from app.memory import add_turn, clear_session, get_history
from app.rag_chain import generate_with_shared_retrieval


BASE_DIR = Path(__file__).resolve().parent
QUESTIONS_FILE = BASE_DIR / "questions.csv"


def score_overlap(response: str, expected_context: str) -> float:
    expected = set(expected_context.lower().split())
    actual = set(response.lower().split())
    if not expected:
        return 0.0
    return len(expected & actual) / len(expected)


def main():
    with QUESTIONS_FILE.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    metrics = []
    for row in rows:
        session_id = row["session_id"]
        if row["turn"] == "1":
            clear_session(session_id)
        history = get_history(session_id)
        started = time.perf_counter()
        result = generate_with_shared_retrieval(row["question"], history=history, backend_name="openai")
        latency_ms = round((time.perf_counter() - started) * 1000)
        coherence = score_overlap(result["response"], row["expected_context"])
        metrics.append(
            {
                "session_id": session_id,
                "turn": row["turn"],
                "latency_ms": latency_ms,
                "source_count": len(result["sources"]),
                "grounded_flag": "yes" if result["sources"] else "no",
                "coherence_score": coherence,
            }
        )
        add_turn(session_id, "user", row["question"])
        add_turn(session_id, "assistant", result["response"])

    print("Version B evaluation scaffold executed.")
    print("Use these metrics as a starting point for Version A vs Version B comparisons:")
    for item in metrics:
        print(item)


if __name__ == "__main__":
    main()
