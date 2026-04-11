from __future__ import annotations

from typing import Any

from core.utils import FALLBACK_ANSWER, confidence_label, score_candidate
from models.finetuned_mode import generate_finetuned_response
from models.openai_mode import generate_openai_response


ROUTE_REASON_LABELS = {
    "image_reasoning_prefer_openai": "OpenAI selected because image reasoning is only available on the multimodal path",
    "fine_tuned_unavailable": "Fine-Tuned unavailable in this environment",
    "openai_unavailable": "OpenAI unavailable, using Fine-Tuned path",
    "low_retrieval_prefer_openai": "OpenAI selected due to limited retrieval confidence",
    "low_retrieval_openai_unavailable": "Fine-Tuned selected because OpenAI was unavailable during low-confidence retrieval",
    "candidate_scoring_win_openai": "OpenAI selected based on stronger candidate scoring",
    "candidate_scoring_win_fine_tuned": "Fine-Tuned selected based on stronger candidate scoring",
    "candidate_score_tie_prefer_openai": "Scores tied, OpenAI selected as stable default",
    "candidate_score_tie_prefer_fine_tuned": "Scores tied, Fine-Tuned selected as preferred fallback",
    "no_retrieval_results": "No supporting retrieval context was found",
    "no_models_available": "No generation backends available",
}


def run_auto_mode(question: str, retrieval: dict, uploaded_images: list | None = None, prefer_openai_on_tie: bool = True) -> dict:
    documents = retrieval["documents"]
    uploaded_images = uploaded_images or []

    if not documents and not uploaded_images:
        return _build_auto_response(
            answer=(
                "I could not find enough relevant supporting context for this question. "
                "Try asking in a more specific way or upload a related document for better grounding."
            ),
            backend="Auto",
            model_name="auto",
            latency_ms=0,
            confidence="Low",
            available=False,
            score=score_candidate(question, FALLBACK_ANSWER, [], 0),
            route_reason="no_retrieval_results",
            comparison={"openai": None, "finetuned": None},
            candidate_scores={"openai": None, "fine_tuned": None},
        )

    openai_result = _normalize_candidate(question, retrieval, generate_openai_response(question, retrieval, uploaded_images=uploaded_images))
    finetuned_result = _normalize_candidate(question, retrieval, generate_finetuned_response(question, retrieval, uploaded_images=uploaded_images))

    if uploaded_images and openai_result["available"]:
        return _finalize_winner(
            winner=openai_result,
            route_reason="image_reasoning_prefer_openai",
            comparison={"openai": openai_result, "finetuned": finetuned_result},
            candidate_scores={"openai": None, "fine_tuned": None},
        )

    if retrieval["weak_retrieval"]:
        if openai_result["available"]:
            cautious_answer = _prepend_low_confidence_note(openai_result["answer"])
            openai_result = dict(openai_result)
            openai_result["answer"] = cautious_answer
            openai_result["confidence"] = "Low"
            openai_result["score"] = score_candidate(question, cautious_answer, documents, openai_result["latency_ms"])
            return _finalize_winner(
                winner=openai_result,
                route_reason="low_retrieval_prefer_openai",
                comparison={"openai": openai_result, "finetuned": finetuned_result},
                candidate_scores={"openai": None, "fine_tuned": None},
            )
        if finetuned_result["available"]:
            cautious_answer = _prepend_low_confidence_note(finetuned_result["answer"])
            finetuned_result = dict(finetuned_result)
            finetuned_result["answer"] = cautious_answer
            finetuned_result["confidence"] = "Low"
            finetuned_result["score"] = score_candidate(question, cautious_answer, documents, finetuned_result["latency_ms"])
            return _finalize_winner(
                winner=finetuned_result,
                route_reason="low_retrieval_openai_unavailable",
                comparison={"openai": openai_result, "finetuned": finetuned_result},
                candidate_scores={"openai": None, "fine_tuned": None},
            )

    if openai_result["available"] and not finetuned_result["available"]:
        return _finalize_winner(
            winner=openai_result,
            route_reason="fine_tuned_unavailable",
            comparison={"openai": openai_result, "finetuned": finetuned_result},
            candidate_scores={"openai": None, "fine_tuned": None},
        )

    if finetuned_result["available"] and not openai_result["available"]:
        return _finalize_winner(
            winner=finetuned_result,
            route_reason="openai_unavailable",
            comparison={"openai": openai_result, "finetuned": finetuned_result},
            candidate_scores={"openai": None, "fine_tuned": None},
        )

    if not openai_result["available"] and not finetuned_result["available"]:
        fallback_backend = openai_result if openai_result.get("answer") else finetuned_result
        return _build_auto_response(
            answer=fallback_backend.get("answer") or FALLBACK_ANSWER,
            backend="Auto",
            model_name="auto",
            latency_ms=0,
            confidence="Low",
            available=False,
            score=score_candidate(question, fallback_backend.get("answer") or FALLBACK_ANSWER, documents, 0),
            route_reason="no_models_available",
            comparison={"openai": openai_result, "finetuned": finetuned_result},
            candidate_scores={"openai": None, "fine_tuned": None},
        )

    openai_score = _score_answer(question, openai_result["answer"], documents, openai_result["latency_ms"], "openai")
    finetuned_score = _score_answer(question, finetuned_result["answer"], documents, finetuned_result["latency_ms"], "fine_tuned")
    candidate_scores = {"openai": round(openai_score, 3), "fine_tuned": round(finetuned_score, 3)}

    if openai_score > finetuned_score:
        return _finalize_winner(
            winner=openai_result,
            route_reason="candidate_scoring_win_openai",
            comparison={"openai": openai_result, "finetuned": finetuned_result},
            candidate_scores=candidate_scores,
        )
    if finetuned_score > openai_score:
        return _finalize_winner(
            winner=finetuned_result,
            route_reason="candidate_scoring_win_fine_tuned",
            comparison={"openai": openai_result, "finetuned": finetuned_result},
            candidate_scores=candidate_scores,
        )

    winner = openai_result if prefer_openai_on_tie else finetuned_result
    route_reason = "candidate_score_tie_prefer_openai" if prefer_openai_on_tie else "candidate_score_tie_prefer_fine_tuned"
    return _finalize_winner(
        winner=winner,
        route_reason=route_reason,
        comparison={"openai": openai_result, "finetuned": finetuned_result},
        candidate_scores=candidate_scores,
    )


def _normalize_candidate(question: str, retrieval: dict, candidate: dict) -> dict:
    normalized = dict(candidate)
    normalized.setdefault("answer", "")
    normalized.setdefault("backend", "Unknown")
    normalized.setdefault("model_name", normalized["backend"])
    normalized.setdefault("latency_ms", 0)
    normalized.setdefault("confidence", _candidate_confidence(question, normalized.get("answer", ""), retrieval))
    normalized.setdefault("available", False)
    normalized.setdefault(
        "score",
        score_candidate(question, normalized.get("answer", ""), retrieval["documents"], normalized.get("latency_ms", 0)),
    )
    return normalized


def _score_answer(question: str, answer: str, documents: list[Any], latency_ms: int, model_name: str) -> float:
    base = score_candidate(question, answer, documents, latency_ms)
    clarity = _score_clarity(answer)
    reliability = 0.90 if model_name == "openai" else 0.78
    return (
        0.40 * base["groundedness"]
        + 0.25 * base["completeness"]
        + 0.15 * clarity
        + 0.10 * reliability
        + 0.10 * base["latency"]
    )


def _score_clarity(answer: str) -> float:
    if not answer or answer == FALLBACK_ANSWER:
        return 0.0
    score = 0.0
    word_count = len(answer.split())
    paragraphs = [paragraph.strip() for paragraph in answer.split("\n") if paragraph.strip()]

    if 20 <= word_count <= 250:
        score += 0.35
    elif 10 <= word_count <= 350:
        score += 0.25

    if len(paragraphs) >= 2:
        score += 0.25
    if answer[0].isupper():
        score += 0.10
    if any(token in answer.lower() for token in ["this means", "in practice", "for example", "for instance"]):
        score += 0.10
    if not any(token in answer.lower() for token in ["error", "traceback", "exception"]):
        score += 0.20
    return max(0.0, min(score, 1.0))


def _candidate_confidence(question: str, answer: str, retrieval: dict) -> str:
    return confidence_label(answer, len(retrieval["sources"]), retrieval.get("overlap", 0.0))


def _prepend_low_confidence_note(answer: str) -> str:
    return (
        "I found limited supporting context for this question, so the answer may be incomplete.\n\n"
        f"{answer or FALLBACK_ANSWER}"
    )


def _build_auto_response(
    answer: str,
    backend: str,
    model_name: str,
    latency_ms: int,
    confidence: str,
    available: bool,
    score: dict,
    route_reason: str,
    comparison: dict,
    candidate_scores: dict,
) -> dict:
    return {
        "answer": answer,
        "backend": backend,
        "model_name": model_name,
        "latency_ms": latency_ms,
        "confidence": confidence,
        "available": available,
        "score": score,
        "route_reason": route_reason,
        "selection_reason": ROUTE_REASON_LABELS.get(route_reason, route_reason),
        "comparison": comparison,
        "candidate_scores": candidate_scores,
    }


def _finalize_winner(winner: dict, route_reason: str, comparison: dict, candidate_scores: dict) -> dict:
    finalized = dict(winner)
    finalized["backend"] = f"Auto -> {winner['backend']}"
    finalized["route_reason"] = route_reason
    finalized["selection_reason"] = ROUTE_REASON_LABELS.get(route_reason, route_reason)
    finalized["comparison"] = comparison
    finalized["candidate_scores"] = candidate_scores
    return finalized
