import csv
from pathlib import Path
from statistics import mean

from app.memory import add_turn, clear_session, get_history
from app.rag_chain import get_rag_response
from app.summarizer import truncate_or_summarize


BASE_DIR = Path(__file__).resolve().parent
QUESTIONS_FILE = BASE_DIR / "questions.csv"
SESSION_ID = "coherence-eval"


def score_coherence(response: str, expected_context: str) -> float:
    expected_words = set(expected_context.lower().split())
    response_words = set(response.lower().split())
    if not expected_words:
        return 0.0
    overlap = expected_words & response_words
    return len(overlap) / len(expected_words)


def load_questions():
    with QUESTIONS_FILE.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def run_conversation(rows, use_memory: bool) -> list[dict]:
    clear_session(SESSION_ID)
    results = []
    for row in rows:
        history = get_history(SESSION_ID) if use_memory else []
        history = truncate_or_summarize(history, llm=None) if use_memory else []
        result = get_rag_response(row["question"], history=history)
        score = score_coherence(result["response"], row["expected_context"])
        results.append(
            {
                "conversation_id": row["conversation_id"],
                "turn": row["turn"],
                "question": row["question"],
                "score": score,
                "response": result["response"],
                "use_memory": use_memory,
            }
        )
        if use_memory:
            add_turn(SESSION_ID, "user", row["question"])
            add_turn(SESSION_ID, "assistant", result["response"])
    return results


def average_score(results: list[dict]) -> float:
    return mean(item["score"] for item in results) if results else 0.0


def main():
    rows = load_questions()
    without_memory = run_conversation(rows, use_memory=False)
    with_memory = run_conversation(rows, use_memory=True)

    score_off = average_score(without_memory)
    score_on = average_score(with_memory)
    improvement = ((score_on - score_off) / score_off * 100) if score_off else 0.0

    print("=== Conversational Memory Evaluation ===")
    print(f"Turns evaluated: {len(rows)}")
    print(f"Average coherence score (memory OFF): {score_off:.3f}")
    print(f"Average coherence score (memory ON):  {score_on:.3f}")
    print(f"Relative improvement:                 {improvement:.1f}%")
    print()
    print("Use the printed improvement only if it matches your real run.")


if __name__ == "__main__":
    main()
