from __future__ import annotations

import os
import time

import streamlit as st
from langchain_openai import ChatOpenAI

from core.prompts import OPENAI_SYSTEM_PROMPT, build_model_prompt
from core.utils import FALLBACK_ANSWER, confidence_label, extractive_answer, retrieval_overlap, score_candidate, simple_factual_query


@st.cache_resource(show_spinner=False)
def get_openai_llm(model_name: str, api_key: str) -> ChatOpenAI:
    return ChatOpenAI(model=model_name, api_key=api_key, temperature=0.1, max_tokens=260)


def generate_openai_response(question: str, retrieval: dict) -> dict:
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    model_name = os.environ.get("OPENAI_MODEL", "gpt-4o-mini").strip()

    if not api_key:
        return {
            "answer": "OpenAI mode is unavailable because OPENAI_API_KEY is not configured.",
            "backend": "OpenAI",
            "model_name": model_name,
            "latency_ms": 0,
            "confidence": "Low",
            "score": {"groundedness": 0.0, "completeness": 0.0, "latency": 0.0, "total": 0.0},
            "available": False,
        }

    start = time.perf_counter()
    documents = retrieval["documents"]

    if retrieval["weak_retrieval"]:
        answer = FALLBACK_ANSWER
    elif simple_factual_query(question) and documents:
        answer = extractive_answer(question, documents) or FALLBACK_ANSWER
    else:
        llm = get_openai_llm(model_name, api_key)
        prompt = build_model_prompt(OPENAI_SYSTEM_PROMPT, question, retrieval["context"])
        answer = llm.invoke(prompt).content.strip() or FALLBACK_ANSWER

    latency_ms = round((time.perf_counter() - start) * 1000)
    overlap = retrieval_overlap(question, documents)
    return {
        "answer": answer,
        "backend": "OpenAI",
        "model_name": model_name,
        "latency_ms": latency_ms,
        "confidence": confidence_label(answer, len(retrieval["sources"]), overlap),
        "score": score_candidate(question, answer, documents, latency_ms),
        "available": True,
    }
