from __future__ import annotations

import hashlib
import os
import re
import time
from pathlib import Path
from typing import Any

FALLBACK_ANSWER = (
    "I don't have sufficient support in the retrieved banking material to answer that confidently."
)
STOPWORDS = {
    "what",
    "which",
    "when",
    "where",
    "why",
    "how",
    "does",
    "about",
    "this",
    "that",
    "from",
    "with",
    "have",
    "will",
    "into",
    "your",
    "their",
    "there",
    "them",
    "just",
}


def env_setting(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def list_base_knowledge_files() -> list[Path]:
    return sorted(project_root().glob("*knowledge*.txt"))


def tokenize(text: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9]+", text.lower())


def keyword_tokens(text: str) -> set[str]:
    return {token for token in tokenize(text) if len(token) > 2 and token not in STOPWORDS}


def source_label(metadata: dict[str, Any]) -> str:
    source = metadata.get("source", "unknown")
    page = metadata.get("page")
    if page:
        return f"{source} (page {page})"
    return str(source)


def preview_text(text: str, limit: int = 280) -> str:
    normalized = re.sub(r"\s+", " ", text).strip()
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3].rstrip() + "..."


def format_context_sections(documents: list[Any], limit: int = 480) -> str:
    sections = []
    for doc in documents:
        label = source_label(doc.metadata)
        sections.append(f"[Source: {label}]\n{preview_text(doc.page_content, limit)}")
    return "\n\n".join(sections)


def retrieval_overlap(question: str, documents: list[Any]) -> float:
    if not documents:
        return 0.0
    question_terms = keyword_tokens(question)
    if not question_terms:
        return 0.0
    corpus = " ".join(doc.page_content for doc in documents)
    corpus_terms = keyword_tokens(corpus)
    return len(question_terms & corpus_terms) / max(len(question_terms), 1)


def weak_retrieval(question: str, documents: list[Any]) -> bool:
    if not documents:
        return True
    return retrieval_overlap(question, documents) < 0.18


def simple_factual_query(question: str) -> bool:
    return len(question.split()) <= 11 and not comparison_query(question)


def comparison_query(question: str) -> bool:
    lowered = question.lower()
    return any(term in lowered for term in ("compare", "difference", "versus", "vs", "india", "u.s.", "us"))


def extractive_answer(question: str, documents: list[Any]) -> str:
    if not documents:
        return ""
    keywords = keyword_tokens(question)
    best_sentences: list[tuple[int, str]] = []
    for doc in documents[:2]:
        sentences = re.split(r"(?<=[.!?])\s+", doc.page_content.strip())
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            overlap = len(keywords & keyword_tokens(sentence))
            best_sentences.append((overlap, sentence))
    if not best_sentences:
        return ""
    best_sentences.sort(key=lambda item: item[0], reverse=True)
    selected = [sentence for overlap, sentence in best_sentences if overlap > 0][:2]
    if not selected:
        selected = [sentence for _, sentence in best_sentences[:2]]
    return " ".join(selected).strip()


def confidence_label(answer: str, source_count: int, overlap: float) -> str:
    if not answer or answer == FALLBACK_ANSWER or source_count == 0:
        return "Low"
    if source_count >= 3 or overlap >= 0.5:
        return "High"
    if source_count >= 2 or overlap >= 0.3:
        return "Moderate"
    return "Low"


def completeness_score(question: str, answer: str) -> float:
    if not answer or answer == FALLBACK_ANSWER:
        return 0.0
    overlap = len(keyword_tokens(question) & keyword_tokens(answer))
    answer_len_bonus = min(len(answer.split()) / 80, 1.0)
    return min(1.0, (overlap / max(len(keyword_tokens(question)), 1)) * 0.6 + answer_len_bonus * 0.4)


def groundedness_score(answer: str, documents: list[Any]) -> float:
    if not answer or answer == FALLBACK_ANSWER or not documents:
        return 0.0
    corpus = " ".join(doc.page_content for doc in documents)
    answer_terms = keyword_tokens(answer)
    corpus_terms = keyword_tokens(corpus)
    if not answer_terms:
        return 0.0
    return min(1.0, len(answer_terms & corpus_terms) / len(answer_terms))


def latency_score(latency_ms: float) -> float:
    if latency_ms <= 0:
        return 0.0
    if latency_ms <= 1200:
        return 1.0
    if latency_ms >= 8000:
        return 0.0
    return max(0.0, 1 - ((latency_ms - 1200) / 6800))


def score_candidate(question: str, answer: str, documents: list[Any], latency_ms: float) -> dict[str, float]:
    grounded = groundedness_score(answer, documents)
    completeness = completeness_score(question, answer)
    latency = latency_score(latency_ms)
    total = grounded * 0.5 + completeness * 0.3 + latency * 0.2
    return {
        "groundedness": round(grounded, 3),
        "completeness": round(completeness, 3),
        "latency": round(latency, 3),
        "total": round(total, 3),
    }


def file_signature(uploaded_files: list[Any] | None) -> str:
    if not uploaded_files:
        return ""
    joined = []
    for uploaded in uploaded_files:
        payload = uploaded.getvalue()
        digest = hashlib.md5(payload).hexdigest()
        joined.append(f"{uploaded.name}:{len(payload)}:{digest}")
    return "|".join(joined)


def now_ms() -> float:
    return time.perf_counter() * 1000
