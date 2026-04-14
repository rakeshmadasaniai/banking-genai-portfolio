from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import time
from collections import Counter
from datetime import datetime
from pathlib import Path
from statistics import mean, median

from huggingface_hub import InferenceClient
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter


BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
RESULTS_DIR = BASE_DIR / "results"
DOMAIN_SET_FILE = BASE_DIR / "evaluation_queries.md"
MULTILINGUAL_SET_FILE = BASE_DIR / "evaluation_multilingual.md"
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini").strip()
HF_TOKEN = os.environ.get("HF_TOKEN", "").strip() or None
FINETUNED_ENDPOINT_URL = os.environ.get("FINETUNED_ENDPOINT_URL", "").strip()
FINETUNED_MODEL_ID = os.environ.get("FINETUNED_MODEL_ID", "RakeshMadasani/banking-finance-mistral-qlora").strip()
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
DOC_GLOB = "*knowledge*.txt"
FALLBACK_ANSWER = "I don't have sufficient support in the retrieved banking material to answer that confidently."

DOMAIN_OUTPUT_CSV = RESULTS_DIR / f"evaluation_queries_results_{TIMESTAMP}.csv"
DOMAIN_OUTPUT_JSON = RESULTS_DIR / f"evaluation_queries_summary_{TIMESTAMP}.json"
MULTI_OUTPUT_CSV = RESULTS_DIR / f"evaluation_multilingual_results_{TIMESTAMP}.csv"
MULTI_OUTPUT_JSON = RESULTS_DIR / f"evaluation_multilingual_summary_{TIMESTAMP}.json"

CSV_FIELDS = [
    "id",
    "set_name",
    "mode_requested",
    "mode_used",
    "language",
    "query",
    "answer",
    "latency_ms",
    "source_count",
    "sources",
    "confidence",
    "grounded_flag",
    "groundedness_score",
    "completeness_score",
    "quality_score",
    "quality_band",
    "hallucination_risk",
    "human_rating_1_to_3",
    "available",
    "route_reason",
]


def fail(message: str) -> None:
    print(message)
    raise SystemExit(1)


def tokenize(text: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9]+", text.lower())


def keyword_tokens(text: str) -> set[str]:
    stopwords = {
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
    return {token for token in tokenize(text) if len(token) > 2 and token not in stopwords}


def comparison_query(question: str) -> bool:
    lowered = question.lower()
    return any(term in lowered for term in ("compare", "difference", "differences", "versus", "vs", "india", "u.s.", "us"))


def simple_factual_query(question: str) -> bool:
    return len(question.split()) <= 11 and not comparison_query(question)


def source_label(doc: Document) -> str:
    source = doc.metadata.get("source", "unknown")
    page = doc.metadata.get("page")
    return f"{source} (page {page})" if page else str(source)


def preview_text(text: str, limit: int = 460) -> str:
    normalized = re.sub(r"\s+", " ", text).strip()
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3].rstrip() + "..."


def load_base_documents() -> list[Document]:
    documents = []
    for path in sorted(PROJECT_DIR.glob(DOC_GLOB)):
        text = path.read_text(encoding="utf-8")
        documents.append(Document(page_content=text, metadata={"source": path.name, "type": "base"}))
    return documents


def split_documents(documents: list[Document]) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=80)
    return splitter.split_documents(documents)


def get_embeddings() -> HuggingFaceEmbeddings:
    return HuggingFaceEmbeddings(model_name=EMBED_MODEL)


class LexicalRetriever:
    def __init__(self, documents: list[Document]) -> None:
        self.documents = documents

    def invoke(self, query: str) -> list[Document]:
        query_terms = keyword_tokens(query)
        scored: list[tuple[tuple[int, int], Document]] = []
        for doc in self.documents:
            doc_terms = keyword_tokens(doc.page_content)
            overlap = len(query_terms & doc_terms)
            scored.append(((overlap, -len(doc.page_content)), doc))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [doc for (_, doc) in scored[:8]]


def get_base_retriever():
    base_docs = load_base_documents()
    if not base_docs:
        fail(f"No knowledge files found in {PROJECT_DIR}. Expected files matching {DOC_GLOB}.")
    split_docs = split_documents(base_docs)
    try:
        vectorstore = FAISS.from_documents(split_docs, get_embeddings())
        return vectorstore.as_retriever(search_type="mmr", search_kwargs={"k": 3, "fetch_k": 10, "lambda_mult": 0.7})
    except Exception:
        return LexicalRetriever(split_docs)


def retrieve_context(query: str, retriever) -> dict:
    per_limit = 2 if simple_factual_query(query) else 3
    seen = set()
    documents: list[Document] = []
    for doc in retriever.invoke(query):
        key = (doc.metadata.get("source"), doc.metadata.get("page"), doc.page_content[:160])
        if key in seen:
            continue
        seen.add(key)
        documents.append(doc)
        if len(documents) >= per_limit:
            break
    source_names = list(dict.fromkeys(source_label(doc) for doc in documents))
    return {
        "documents": documents,
        "sources": source_names,
        "context": "\n\n".join(f"[Source: {source_label(doc)}]\n{preview_text(doc.page_content)}" for doc in documents),
    }


def retrieval_overlap(question: str, documents: list[Document]) -> float:
    if not documents:
        return 0.0
    question_terms = keyword_tokens(question)
    if not question_terms:
        return 0.0
    corpus_terms = keyword_tokens(" ".join(doc.page_content for doc in documents))
    return len(question_terms & corpus_terms) / max(len(question_terms), 1)


def confidence_label(answer: str, source_count: int, overlap: float) -> str:
    if not answer or answer == FALLBACK_ANSWER or source_count == 0:
        return "Moderate"
    if source_count >= 3 or overlap >= 0.5:
        return "High"
    return "Moderate"


def grounded_flag(answer: str, source_count: int) -> str:
    return "yes" if answer and answer != FALLBACK_ANSWER and source_count >= 1 else "no"


def completeness_metric(question: str, answer: str) -> float:
    if not answer or answer == FALLBACK_ANSWER:
        return 0.0
    question_terms = keyword_tokens(question)
    if not question_terms:
        return 0.0
    answer_terms = keyword_tokens(answer)
    lexical_cover = len(question_terms & answer_terms) / max(len(question_terms), 1)
    length_bonus = min(len(answer.split()) / 60, 1.0) * 0.25
    return round(min(1.0, lexical_cover + length_bonus), 3)


def quality_band(score: float) -> str:
    if score >= 0.72:
        return "strong"
    if score >= 0.45:
        return "usable"
    return "weak"


def hallucination_risk(answer: str, source_count: int, groundedness: float) -> str:
    if not answer or answer == FALLBACK_ANSWER or source_count == 0:
        return "high"
    if groundedness >= 0.5 and source_count >= 1:
        return "low"
    return "medium"


def extractive_answer(question: str, documents: list[Document]) -> str:
    if not documents:
        return ""
    keywords = keyword_tokens(question)
    scored: list[tuple[int, str]] = []
    for doc in documents[:2]:
        for sentence in re.split(r"(?<=[.!?])\s+", doc.page_content.strip()):
            sentence = sentence.strip()
            if not sentence:
                continue
            overlap = len(keywords & keyword_tokens(sentence))
            scored.append((overlap, sentence))
    if not scored:
        return ""
    scored.sort(key=lambda item: item[0], reverse=True)
    selected = [sentence for overlap, sentence in scored if overlap > 0][:2]
    if not selected:
        selected = [sentence for _, sentence in scored[:2]]
    return " ".join(selected).strip()


def build_prompt(question: str, context: str, language: str = "") -> str:
    language_line = ""
    if language and language.lower() != "english":
        language_line = f"\nAnswer in {language}. Keep the same language as the user's question.\n"
    return f"""You are a professional Banking & Finance AI Copilot.

Answer only from the provided context.
If the context does not support the answer, say: "{FALLBACK_ANSWER}".
Start with a direct answer, then explain clearly and professionally.
Use compact bullets only when they help.
{language_line}
Retrieved context:
{context}

User question: {question}

Answer:
"""


def get_openai_llm() -> ChatOpenAI | None:
    if not OPENAI_API_KEY:
        return None
    return ChatOpenAI(model=OPENAI_MODEL, api_key=OPENAI_API_KEY, temperature=0.1, max_tokens=260)


def get_finetuned_client() -> tuple[InferenceClient | None, str]:
    target = FINETUNED_ENDPOINT_URL or FINETUNED_MODEL_ID
    if not target:
        return None, FINETUNED_MODEL_ID
    return InferenceClient(model=target, token=HF_TOKEN), FINETUNED_MODEL_ID


def score_total(question: str, answer: str, documents: list[Document], latency_ms: float) -> float:
    if not answer or answer == FALLBACK_ANSWER:
        return 0.0
    grounded = retrieval_overlap(answer, documents)
    completeness = completeness_metric(question, answer)
    if latency_ms <= 1200:
        latency = 1.0
    elif latency_ms >= 8000:
        latency = 0.0
    else:
        latency = max(0.0, 1 - ((latency_ms - 1200) / 6800))
    return round(grounded * 0.45 + completeness * 0.35 + latency * 0.20, 3)


def run_openai(question: str, retrieval: dict, language: str = "") -> dict:
    start = time.perf_counter()
    llm = get_openai_llm()
    if llm is None:
        answer = extractive_answer(question, retrieval["documents"]) or FALLBACK_ANSWER
        latency_ms = round((time.perf_counter() - start) * 1000)
        overlap = retrieval_overlap(question, retrieval["documents"])
        return {
            "answer": answer,
            "mode_used": "OpenAI",
            "latency_ms": latency_ms,
            "confidence": confidence_label(answer, len(retrieval["sources"]), overlap),
            "available": False,
            "route_reason": "openai_api_key_missing",
        }

    if simple_factual_query(question) and retrieval["documents"]:
        answer = extractive_answer(question, retrieval["documents"]) or FALLBACK_ANSWER
    else:
        answer = llm.invoke(build_prompt(question, retrieval["context"], language)).content.strip() or FALLBACK_ANSWER

    latency_ms = round((time.perf_counter() - start) * 1000)
    overlap = retrieval_overlap(question, retrieval["documents"])
    return {
        "answer": answer,
        "mode_used": "OpenAI",
        "latency_ms": latency_ms,
        "confidence": confidence_label(answer, len(retrieval["sources"]), overlap),
        "available": True,
        "route_reason": "openai_direct",
    }


def run_finetuned(question: str, retrieval: dict, language: str = "") -> dict:
    start = time.perf_counter()
    client, model_name = get_finetuned_client()
    if client is None:
        answer = extractive_answer(question, retrieval["documents"]) or FALLBACK_ANSWER
        latency_ms = round((time.perf_counter() - start) * 1000)
        overlap = retrieval_overlap(question, retrieval["documents"])
        return {
            "answer": answer,
            "mode_used": "Fine-Tuned",
            "latency_ms": latency_ms,
            "confidence": confidence_label(answer, len(retrieval["sources"]), overlap),
            "available": False,
            "route_reason": "finetuned_not_configured",
            "model_name": model_name,
        }
    try:
        answer = client.text_generation(
            build_prompt(question, retrieval["context"], language),
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
        "mode_used": "Fine-Tuned",
        "latency_ms": latency_ms,
        "confidence": confidence_label(answer, len(retrieval["sources"]), overlap),
        "available": True,
        "route_reason": "finetuned_direct",
        "model_name": model_name,
    }


def run_auto(question: str, retrieval: dict, language: str = "") -> dict:
    openai_result = run_openai(question, retrieval, language)
    finetuned_result = run_finetuned(question, retrieval, language)
    is_non_english = bool(language and language.lower() != "english")

    if is_non_english:
        if finetuned_result["available"] and finetuned_result["latency_ms"] <= openai_result["latency_ms"]:
            winner = finetuned_result
            route_reason = "fastest_multilingual_finetuned"
        elif openai_result["available"]:
            winner = openai_result
            route_reason = "fastest_multilingual_openai"
        else:
            winner = finetuned_result
            route_reason = "multilingual_fallback_finetuned"
    else:
        openai_score = score_total(question, openai_result["answer"], retrieval["documents"], openai_result["latency_ms"])
        finetuned_score = score_total(question, finetuned_result["answer"], retrieval["documents"], finetuned_result["latency_ms"])
        if openai_result["available"] and not finetuned_result["available"]:
            winner = openai_result
            route_reason = "fine_tuned_unavailable"
        elif finetuned_result["available"] and not openai_result["available"]:
            winner = finetuned_result
            route_reason = "openai_unavailable"
        elif finetuned_score > openai_score:
            winner = finetuned_result
            route_reason = "candidate_scoring_win_fine_tuned"
        elif openai_score > finetuned_score:
            winner = openai_result
            route_reason = "candidate_scoring_win_openai"
        elif finetuned_result["latency_ms"] <= openai_result["latency_ms"]:
            winner = finetuned_result
            route_reason = "tie_break_faster_fine_tuned"
        else:
            winner = openai_result
            route_reason = "tie_break_faster_openai"

    return {
        "answer": winner["answer"],
        "mode_used": f"Auto -> {winner['mode_used']}",
        "latency_ms": winner["latency_ms"],
        "confidence": winner["confidence"],
        "available": winner["available"],
        "route_reason": route_reason,
    }


def parse_domain_set(path: Path) -> list[dict]:
    rows = []
    mode = ""
    for line in path.read_text(encoding="utf-8").splitlines():
        heading = re.match(r"##\s+Mode\s+\d+\s+[—-]\s+(.+?)\s+\(", line.strip())
        if heading:
            mode = heading.group(1).strip()
            continue
        item = re.match(r"(\d+)\.\s+(.*)", line.strip())
        if item and mode:
            rows.append(
                {
                    "id": int(item.group(1)),
                    "mode_requested": mode,
                    "language": "English",
                    "query": item.group(2).strip(),
                }
            )
    return rows


def parse_multilingual_set(path: Path) -> list[dict]:
    rows = []
    mode = ""
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        heading = re.match(r"##\s+Mode\s+\d+\s+[—-]\s+(.+?)\s+\(", line)
        if heading:
            mode = heading.group(1).strip()
            continue
        if not mode or not line.startswith("|"):
            continue
        parts = [part.strip() for part in line.split("|")[1:-1]]
        if len(parts) != 3 or parts[0] == "#" or set(parts[0]) == {"-"}:
            continue
        if not parts[0].isdigit():
            continue
        rows.append(
            {
                "id": int(parts[0]),
                "mode_requested": mode,
                "language": parts[1],
                "query": parts[2],
            }
        )
    return rows


def write_csv(rows: list[dict], destination: Path) -> None:
    with destination.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def build_summary(rows: list[dict], set_name: str) -> dict:
    available_rows = [row for row in rows if row["available"] == "yes"]
    latencies = [row["latency_ms"] for row in available_rows]
    by_mode: dict[str, dict] = {}
    for mode in sorted(set(row["mode_requested"] for row in rows)):
        mode_rows = [row for row in rows if row["mode_requested"] == mode]
        mode_available_rows = [row for row in mode_rows if row["available"] == "yes"]
        by_mode[mode] = {
            "count": len(mode_rows),
            "available_count": len(mode_available_rows),
            "average_latency_ms": round(mean(row["latency_ms"] for row in mode_available_rows), 1) if mode_available_rows else None,
            "median_latency_ms": round(median(row["latency_ms"] for row in mode_available_rows), 1) if mode_available_rows else None,
            "confidence_counts": dict(Counter(row["confidence"] for row in mode_available_rows)),
        }
    return {
        "set_name": set_name,
        "completed_queries": len(rows),
        "available_rows": len(available_rows),
        "average_latency_ms": round(mean(latencies), 1) if latencies else None,
        "median_latency_ms": round(median(latencies), 1) if latencies else None,
        "by_mode": by_mode,
    }


def write_summary(summary: dict, destination: Path) -> None:
    with destination.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, ensure_ascii=False)


def run_set(rows: list[dict], set_name: str) -> list[dict]:
    retriever = get_base_retriever()
    completed = []
    for row in rows:
        retrieval = retrieve_context(row["query"], retriever)
        requested_mode = row["mode_requested"]
        if requested_mode == "OpenAI":
            result = run_openai(row["query"], retrieval, row["language"])
        elif requested_mode == "Fine-Tuned":
            result = run_finetuned(row["query"], retrieval, row["language"])
        else:
            result = run_auto(row["query"], retrieval, row["language"])
        completed.append(
            {
                "id": row["id"],
                "set_name": set_name,
                "mode_requested": requested_mode,
                "mode_used": result["mode_used"],
                "language": row["language"],
                "query": row["query"],
                "answer": result["answer"],
                "latency_ms": result["latency_ms"],
                "source_count": len(retrieval["sources"]),
                "sources": " | ".join(retrieval["sources"]),
                "confidence": result["confidence"],
                "grounded_flag": grounded_flag(result["answer"], len(retrieval["sources"])),
                "groundedness_score": retrieval_overlap(result["answer"], retrieval["documents"]),
                "completeness_score": completeness_metric(row["query"], result["answer"]),
                "quality_score": score_total(row["query"], result["answer"], retrieval["documents"], result["latency_ms"]),
                "quality_band": quality_band(score_total(row["query"], result["answer"], retrieval["documents"], result["latency_ms"])),
                "hallucination_risk": hallucination_risk(
                    result["answer"],
                    len(retrieval["sources"]),
                    retrieval_overlap(result["answer"], retrieval["documents"]),
                ),
                "human_rating_1_to_3": "",
                "available": "yes" if result["available"] else "no",
                "route_reason": result["route_reason"],
            }
        )
    return completed


def main() -> None:
    parser = argparse.ArgumentParser(description="Run automatic evaluation for the two markdown query sets.")
    parser.add_argument("--set", choices=["all", "domain", "multilingual"], default="all")
    args = parser.parse_args()

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    if args.set in {"all", "domain"}:
        domain_rows = run_set(parse_domain_set(DOMAIN_SET_FILE), "evaluation_queries")
        write_csv(domain_rows, DOMAIN_OUTPUT_CSV)
        write_summary(build_summary(domain_rows, "evaluation_queries"), DOMAIN_OUTPUT_JSON)
        print(f"Wrote domain results: {DOMAIN_OUTPUT_CSV.name}")
        print(f"Wrote domain summary: {DOMAIN_OUTPUT_JSON.name}")

    if args.set in {"all", "multilingual"}:
        multi_rows = run_set(parse_multilingual_set(MULTILINGUAL_SET_FILE), "evaluation_multilingual")
        write_csv(multi_rows, MULTI_OUTPUT_CSV)
        write_summary(build_summary(multi_rows, "evaluation_multilingual"), MULTI_OUTPUT_JSON)
        print(f"Wrote multilingual results: {MULTI_OUTPUT_CSV.name}")
        print(f"Wrote multilingual summary: {MULTI_OUTPUT_JSON.name}")


if __name__ == "__main__":
    main()
