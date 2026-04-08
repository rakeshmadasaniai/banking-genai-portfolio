from __future__ import annotations

from models.finetuned_mode import generate_finetuned_response
from models.openai_mode import generate_openai_response


def run_auto_mode(question: str, retrieval: dict) -> dict:
    # Auto mode retrieves context once, asks each backend to answer on the same grounding,
    # then chooses the stronger candidate from a simple weighted score:
    # groundedness > completeness > latency.
    openai_result = generate_openai_response(question, retrieval)
    finetuned_result = generate_finetuned_response(question, retrieval)
    candidates = [candidate for candidate in (openai_result, finetuned_result) if candidate["available"]]
    winner = max(candidates, key=lambda candidate: candidate["score"]["total"]) if candidates else openai_result
    winner = dict(winner)
    winner["backend"] = f"Auto -> {winner['backend']}"
    winner["selection_reason"] = (
        "Selected from candidates using groundedness, completeness, and latency scoring on shared retrieved context."
    )
    winner["comparison"] = {"openai": openai_result, "finetuned": finetuned_result}
    return winner
