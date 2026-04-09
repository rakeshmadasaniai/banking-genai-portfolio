from __future__ import annotations

import base64
import os
import time

import streamlit as st
from langchain_openai import ChatOpenAI
from openai import OpenAI

from core.prompts import OPENAI_SYSTEM_PROMPT, build_model_prompt
from core.utils import FALLBACK_ANSWER, confidence_label, extractive_answer, retrieval_overlap, score_candidate, simple_factual_query


@st.cache_resource(show_spinner=False)
def get_openai_llm(model_name: str, api_key: str) -> ChatOpenAI:
    return ChatOpenAI(model=model_name, api_key=api_key, temperature=0.1, max_tokens=260)


def _vision_answer(api_key: str, model_name: str, question: str, retrieval: dict, uploaded_images: list) -> str:
    client = OpenAI(api_key=api_key)
    prompt = build_model_prompt(OPENAI_SYSTEM_PROMPT, question, retrieval["context"] or "No supporting text context was retrieved.")
    content = [{"type": "text", "text": prompt}]
    for uploaded_image in uploaded_images[:3]:
        image_bytes = uploaded_image.getvalue()
        mime_type = getattr(uploaded_image, "type", None) or "image/png"
        encoded = base64.b64encode(image_bytes).decode("utf-8")
        content.append(
            {
                "type": "image_url",
                "image_url": {"url": f"data:{mime_type};base64,{encoded}"},
            }
        )

    response = client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": content}],
        max_tokens=320,
        temperature=0.1,
    )
    return (response.choices[0].message.content or "").strip()


def generate_openai_response(question: str, retrieval: dict, uploaded_images: list | None = None) -> dict:
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    model_name = os.environ.get("OPENAI_MODEL", "gpt-4o-mini").strip()
    uploaded_images = uploaded_images or []

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

    if uploaded_images:
        answer = _vision_answer(api_key, model_name, question, retrieval, uploaded_images) or FALLBACK_ANSWER
    elif retrieval["weak_retrieval"]:
        answer = FALLBACK_ANSWER
    elif simple_factual_query(question) and documents:
        answer = extractive_answer(question, documents) or FALLBACK_ANSWER
    else:
        llm = get_openai_llm(model_name, api_key)
        prompt = build_model_prompt(OPENAI_SYSTEM_PROMPT, question, retrieval["context"])
        answer = llm.invoke(prompt).content.strip() or FALLBACK_ANSWER

    latency_ms = round((time.perf_counter() - start) * 1000)
    overlap = retrieval_overlap(question, documents) if documents else 0.0
    confidence = confidence_label(answer, len(retrieval["sources"]), overlap)
    if uploaded_images and confidence == "Low":
        confidence = "Moderate"
    return {
        "answer": answer,
        "backend": "OpenAI",
        "model_name": model_name,
        "latency_ms": latency_ms,
        "confidence": confidence,
        "score": score_candidate(question, answer, documents, latency_ms),
        "available": True,
    }
