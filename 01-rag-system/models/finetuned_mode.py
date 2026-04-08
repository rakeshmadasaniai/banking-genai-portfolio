from __future__ import annotations

import os
import time

from huggingface_hub import InferenceClient

from core.prompts import FINETUNED_SYSTEM_PROMPT, build_model_prompt
from core.utils import FALLBACK_ANSWER, confidence_label, extractive_answer, retrieval_overlap, score_candidate


def _build_client() -> tuple[InferenceClient | None, str]:
    endpoint = os.environ.get("FINETUNED_ENDPOINT_URL", "").strip()
    model_id = os.environ.get("FINETUNED_MODEL_ID", "RakeshMadasani/banking-finance-mistral-qlora").strip()
    token = os.environ.get("HF_TOKEN", "").strip() or None
    target = endpoint or model_id
    if not target:
        return None, model_id
    return InferenceClient(model=target, token=token), model_id


def generate_finetuned_response(question: str, retrieval: dict) -> dict:
    client, model_name = _build_client()
    if client is None:
        fallback_answer = extractive_answer(question, retrieval["documents"]) or FALLBACK_ANSWER
        overlap = retrieval_overlap(question, retrieval["documents"])
        return {
            "answer": fallback_answer,
            "backend": "Fine-Tuned",
            "model_name": model_name,
            "latency_ms": 0,
            "confidence": confidence_label(fallback_answer, len(retrieval["sources"]), overlap),
            "score": score_candidate(question, fallback_answer, retrieval["documents"], 0),
            "available": False,
        }

    start = time.perf_counter()
    if retrieval["weak_retrieval"]:
        answer = FALLBACK_ANSWER
    else:
        prompt = build_model_prompt(FINETUNED_SYSTEM_PROMPT, question, retrieval["context"])
        try:
            answer = client.text_generation(
                prompt,
                max_new_tokens=220,
                temperature=0.1,
                return_full_text=False,
            ).strip()
        except Exception:
            answer = ""
    answer = answer or extractive_answer(question, retrieval["documents"]) or FALLBACK_ANSWER
    latency_ms = round((time.perf_counter() - start) * 1000)
    overlap = retrieval_overlap(question, retrieval["documents"])
    return {
        "answer": answer,
        "backend": "Fine-Tuned",
        "model_name": model_name,
        "latency_ms": latency_ms,
        "confidence": confidence_label(answer, len(retrieval["sources"]), overlap),
        "score": score_candidate(question, answer, retrieval["documents"], latency_ms),
        "available": "could not generate" not in answer.lower() and "not configured" not in answer.lower(),
    }
