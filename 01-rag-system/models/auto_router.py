from __future__ import annotations

from core.utils import score_candidate
from models.finetuned_mode import generate_finetuned_response
from models.openai_mode import generate_openai_response


ROUTE_REASON_LABELS = {
    "fine_tuned_unavailable": "Fine-Tuned unavailable in this environment",
    "openai_unavailable": "OpenAI unavailable, using Fine-Tuned path",
    "low_retrieval_prefer_openai": "OpenAI selected due to limited retrieval confidence",
    "candidate_scoring_win_openai": "OpenAI selected based on stronger candidate scoring",
    "candidate_scoring_win_fine_tuned": "Fine-Tuned selected based on stronger candidate scoring",
    "candidate_score_tie_prefer_openai": "Scores tied, OpenAI selected as stable default",
    "no_models_available": "No generation backends available",
}


def _normalize_candidate(question: str, retrieval: dict, candidate: dict) -> dict:
    normalized = dict(candidate)
    normalized.setdefault("backend", "Unknown")
    normalized.setdefault("model_name", normalized["backend"])
    normalized.setdefault("latency_ms", 0)
    normalized.setdefault("confidence", "Low")
    normalized.setdefault("available", False)
    normalized.setdefault(
        "score",
        score_candidate(question, normalized.get("answer", ""), retrieval["documents"], normalized.get("latency_ms", 0)),
    )
    return normalized


def run_auto_mode(question: str, retrieval: dict) -> dict:
    # Auto mode retrieves shared context once, checks routing conditions, then either
    # returns the safest available backend directly or compares candidates on the same
    # retrieved chunks using groundedness, completeness, and latency-aware scoring.
    openai_result = _normalize_candidate(question, retrieval, generate_openai_response(question, retrieval))
    finetuned_result = _normalize_candidate(question, retrieval, generate_finetuned_response(question, retrieval))
    candidate_scores = {"openai": None, "fine_tuned": None}

    if retrieval["weak_retrieval"]:
        if openai_result["available"]:
            winner = dict(openai_result)
            winner["backend"] = f"Auto -> {winner['backend']}"
            winner["route_reason"] = "low_retrieval_prefer_openai"
            winner["selection_reason"] = ROUTE_REASON_LABELS[winner["route_reason"]]
            winner["comparison"] = {"openai": openai_result, "finetuned": finetuned_result}
            winner["candidate_scores"] = candidate_scores
            return winner
        if finetuned_result["available"]:
            winner = dict(finetuned_result)
            winner["backend"] = f"Auto -> {winner['backend']}"
            winner["route_reason"] = "openai_unavailable"
            winner["selection_reason"] = "Retrieval confidence was limited, and only the Fine-Tuned path was available."
            winner["comparison"] = {"openai": openai_result, "finetuned": finetuned_result}
            winner["candidate_scores"] = candidate_scores
            return winner

    if openai_result["available"] and not finetuned_result["available"]:
        winner = dict(openai_result)
        winner["backend"] = f"Auto -> {winner['backend']}"
        winner["route_reason"] = "fine_tuned_unavailable"
        winner["selection_reason"] = ROUTE_REASON_LABELS[winner["route_reason"]]
        winner["comparison"] = {"openai": openai_result, "finetuned": finetuned_result}
        winner["candidate_scores"] = candidate_scores
        return winner

    if finetuned_result["available"] and not openai_result["available"]:
        winner = dict(finetuned_result)
        winner["backend"] = f"Auto -> {winner['backend']}"
        winner["route_reason"] = "openai_unavailable"
        winner["selection_reason"] = ROUTE_REASON_LABELS[winner["route_reason"]]
        winner["comparison"] = {"openai": openai_result, "finetuned": finetuned_result}
        winner["candidate_scores"] = candidate_scores
        return winner

    if not openai_result["available"] and not finetuned_result["available"]:
        winner = dict(openai_result)
        winner["backend"] = "Auto"
        winner["route_reason"] = "no_models_available"
        winner["selection_reason"] = ROUTE_REASON_LABELS[winner["route_reason"]]
        winner["comparison"] = {"openai": openai_result, "finetuned": finetuned_result}
        winner["candidate_scores"] = candidate_scores
        return winner

    openai_score = openai_result["score"]["total"]
    finetuned_score = finetuned_result["score"]["total"]
    candidate_scores = {"openai": openai_score, "fine_tuned": finetuned_score}

    if openai_score > finetuned_score:
        winner = dict(openai_result)
        winner["route_reason"] = "candidate_scoring_win_openai"
    elif finetuned_score > openai_score:
        winner = dict(finetuned_result)
        winner["route_reason"] = "candidate_scoring_win_fine_tuned"
    else:
        winner = dict(openai_result)
        winner["route_reason"] = "candidate_score_tie_prefer_openai"

    winner["backend"] = f"Auto -> {winner['backend']}"
    winner["selection_reason"] = ROUTE_REASON_LABELS[winner["route_reason"]]
    winner["comparison"] = {"openai": openai_result, "finetuned": finetuned_result}
    winner["candidate_scores"] = candidate_scores
    return winner
