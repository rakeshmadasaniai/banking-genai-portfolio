from __future__ import annotations

from models.finetuned_mode import generate_finetuned_response
from models.openai_mode import generate_openai_response


def run_auto_mode(question: str, retrieval: dict) -> dict:
    openai_result = generate_openai_response(question, retrieval)
    finetuned_result = generate_finetuned_response(question, retrieval)
    candidates = [candidate for candidate in (openai_result, finetuned_result) if candidate["available"]]
    winner = max(candidates, key=lambda candidate: candidate["score"]["total"]) if candidates else openai_result
    winner = dict(winner)
    winner["backend"] = f"Auto -> {winner['backend']}"
    winner["comparison"] = {"openai": openai_result, "finetuned": finetuned_result}
    return winner
