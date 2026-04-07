import csv
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter


BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
QUESTIONS_FILE = BASE_DIR / "questions.csv"
OUTPUT_FILE = BASE_DIR / f"batch_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
DOC_GLOB = "*knowledge*.txt"
COMPARISON_TERMS = ("compare", "difference", "differences", "versus", "vs", "india", "u.s.", "us")
FALLBACK_ANSWER = "I don't have sufficient information on that topic in my knowledge base."

RAG_PROMPT = PromptTemplate(
    input_variables=["context", "question"],
    template="""Answer only from the provided context.

If the answer is not supported by the context, say:
"I don't have sufficient information on that topic in my knowledge base."

Be concise and professional.

Context:
{context}

Question: {question}

Answer:""",
)

COMPARISON_RAG_PROMPT = PromptTemplate(
    input_variables=["context", "question"],
    template="""Answer only from the provided context.

If the answer is not supported by the context, say:
"I don't have sufficient information on that topic in my knowledge base."

If the question asks for a comparison, combine facts across the provided source excerpts when each part of the comparison is supported.
Be concise, explicit, and mention the key difference directly.

Context:
{context}

Question: {question}

Answer:""",
)


def fail(message):
    print(message)
    raise SystemExit(1)


def load_text_documents():
    documents = []
    for path in sorted(PROJECT_DIR.glob(DOC_GLOB)):
        text = path.read_text(encoding="utf-8")
        documents.append(Document(page_content=text, metadata={"source": path.name, "type": "base"}))
    return documents


def split_documents(documents):
    splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=80)
    return splitter.split_documents(documents)


def get_embeddings():
    return HuggingFaceEmbeddings(model_name=EMBED_MODEL)


def get_base_index():
    base_docs = load_text_documents()
    if not base_docs:
        fail(
            f"No knowledge files found in {PROJECT_DIR}. "
            "Expected files matching *knowledge*.txt for local evaluation."
        )
    base_chunks = split_documents(base_docs)
    vectorstore = FAISS.from_documents(base_chunks, get_embeddings())
    retriever = vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs={"k": 3, "fetch_k": 10, "lambda_mult": 0.7},
    )
    return retriever


def get_llm():
    if not OPENAI_API_KEY:
        fail("OPENAI_API_KEY is not set. Set it in your shell before running batch_eval.py.")
    return ChatOpenAI(model=OPENAI_MODEL, api_key=OPENAI_API_KEY, temperature=0.1, max_tokens=220)


def source_label(doc):
    source = doc.metadata.get("source", "unknown")
    page = doc.metadata.get("page")
    return f"{source} (page {page})" if page else source


def is_simple_factual_query(query):
    lowered_query = query.lower()
    return len(query.split()) <= 10 and not any(term in lowered_query for term in COMPARISON_TERMS)


def is_comparison_query(query):
    lowered_query = query.lower()
    return any(term in lowered_query for term in COMPARISON_TERMS)


def retrieve_context(query, base_retriever):
    lowered_query = query.lower()
    per_retriever_limit = 2 if len(query.split()) <= 10 and not any(term in lowered_query for term in COMPARISON_TERMS) else 3

    combined = []
    seen = set()
    added = 0
    for doc in base_retriever.invoke(query):
        key = (
            doc.metadata.get("source", "unknown"),
            doc.metadata.get("page", ""),
            doc.page_content[:160],
        )
        if key in seen:
            continue
        seen.add(key)
        combined.append(doc)
        added += 1
        if added >= per_retriever_limit:
            break

    final_limit = 2 if per_retriever_limit == 2 else 4
    return combined[:final_limit]


def build_context(context_docs, char_limit):
    sections = []
    for doc in context_docs:
        label = source_label(doc)
        snippet = doc.page_content[:char_limit].strip()
        sections.append(f"[Source: {label}]\n{snippet}")
    return "\n\n".join(sections)


def boosted_context(question, context_docs, base_context):
    lowered_question = question.lower()
    if not is_comparison_query(question):
        return base_context

    priority_terms = []
    for term in ("ctr", "sar", "fdic", "regulation e", "basel", "kyc", "aml"):
        if term in lowered_question:
            priority_terms.append(term)

    if not priority_terms:
        return base_context

    highlighted = []
    for doc in context_docs:
        sentences = re.split(r"(?<=[.!?])\s+", doc.page_content.strip())
        for sentence in sentences:
            normalized_sentence = sentence.lower()
            if any(term in normalized_sentence for term in priority_terms):
                highlighted.append(f"[Priority source: {source_label(doc)}]\n{sentence.strip()}")
                if len(highlighted) >= 4:
                    break
        if len(highlighted) >= 4:
            break

    if not highlighted:
        return base_context
    return "\n\n".join(highlighted) + "\n\n" + base_context


def extractive_answer(context_docs, question):
    if not context_docs:
        return ""

    keywords = {
        token.lower()
        for token in re.findall(r"[A-Za-z0-9]+", question)
        if len(token) > 3 and token.lower() not in {"what", "does", "work", "works", "covered", "cover", "with", "from", "that", "this"}
    }
    sentences = re.split(r"(?<=[.!?])\s+", context_docs[0].page_content.strip())
    scored = []
    for sentence in sentences:
        sentence_tokens = set(re.findall(r"[A-Za-z0-9]+", sentence.lower()))
        overlap = len(keywords & sentence_tokens)
        if sentence.strip():
            scored.append((overlap, sentence.strip()))

    if not scored:
        return ""

    scored.sort(key=lambda item: item[0], reverse=True)
    best_sentences = [sentence for overlap, sentence in scored if overlap > 0][:2]
    if not best_sentences:
        best_sentences = [sentence for _, sentence in scored[:2]]
    return " ".join(best_sentences).strip()


def confidence_label(source_count, answer_text="", extractive=False):
    normalized_answer = answer_text.strip()
    if normalized_answer == FALLBACK_ANSWER or source_count == 0:
        return "Low"
    if extractive and source_count >= 1:
        return "High"
    if source_count >= 3:
        return "High"
    if source_count in (1, 2):
        return "Moderate"
    return "Low"


def score_response(answer):
    normalized = answer.strip().lower()
    has_answer = bool(answer.strip()) and normalized != FALLBACK_ANSWER.lower()
    cites_source = "[source:" in normalized or "according" in normalized
    is_domain_specific = any(
        word in normalized
        for word in [
            "bank",
            "aml",
            "kyc",
            "fdic",
            "rbi",
            "basel",
            "compliance",
            "regulation",
            "financial",
            "deposit",
            "capital",
        ]
    )
    return {
        "has_answer": has_answer,
        "cites_source": cites_source,
        "is_domain_specific": is_domain_specific,
    }


def run_question(question, retriever, llm):
    start = time.perf_counter()
    context_docs = retrieve_context(question, retriever)
    context_char_limit = 550 if is_comparison_query(question) else 350
    context = build_context(context_docs, context_char_limit)
    context = boosted_context(question, context_docs, context)
    source_names = [source_label(doc) for doc in context_docs]
    unique_sources = list(dict.fromkeys(source_names))

    used_extractive_path = False
    if is_simple_factual_query(question) and unique_sources:
        answer = extractive_answer(context_docs, question) or FALLBACK_ANSWER
        used_extractive_path = answer != FALLBACK_ANSWER
    else:
        prompt_template = COMPARISON_RAG_PROMPT if is_comparison_query(question) else RAG_PROMPT
        prompt_text = prompt_template.format(context=context, question=question)
        answer = llm.invoke(prompt_text).content.strip()

    latency_ms = round((time.perf_counter() - start) * 1000)
    confidence = confidence_label(
        len(unique_sources),
        answer_text=answer,
        extractive=used_extractive_path,
    )
    auto_scores = score_response(answer)

    return {
        "answer": answer,
        "latency_ms": latency_ms,
        "source_count": len(unique_sources),
        "sources": unique_sources,
        "confidence": confidence,
        "grounded_flag": "yes" if answer.strip() != FALLBACK_ANSWER and len(unique_sources) >= 1 else "no",
        **auto_scores,
    }


def load_questions():
    with QUESTIONS_FILE.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_results(results):
    with OUTPUT_FILE.open("w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2)


def print_summary(results):
    avg_latency = sum(row["latency_ms"] for row in results) / len(results)
    avg_sources = sum(row["source_count"] for row in results) / len(results)
    grounded_rate = sum(1 for row in results if row["grounded_flag"] == "yes") / len(results) * 100
    has_answer_rate = sum(1 for row in results if row["has_answer"]) / len(results) * 100
    cites_source_rate = sum(1 for row in results if row["cites_source"]) / len(results) * 100
    domain_specific_rate = sum(1 for row in results if row["is_domain_specific"]) / len(results) * 100

    print()
    print("===== BATCH EVAL SUMMARY =====")
    print(f"Questions tested:      {len(results)}")
    print(f"Average latency:       {avg_latency:.1f} ms")
    print(f"Average sources:       {avg_sources:.1f}")
    print(f"Grounded response:     {grounded_rate:.1f}%")
    print(f"Has answer rate:       {has_answer_rate:.1f}%")
    print(f"Cites source rate:     {cites_source_rate:.1f}%")
    print(f"Domain specific rate:  {domain_specific_rate:.1f}%")
    print(f"Results file:          {OUTPUT_FILE}")


def main():
    print("Loading retrieval index and LLM...")
    retriever = get_base_index()
    llm = get_llm()
    questions = load_questions()

    results = []
    print(f"Running batch evaluation on {len(questions)} questions...")
    for row in questions:
        qid = row["id"]
        question = row["question"]
        category = row["category"]
        print(f"[{qid}/{len(questions)}] {question}")
        result = run_question(question, retriever, llm)
        results.append(
            {
                "id": qid,
                "category": category,
                "question": question,
                **result,
            }
        )
        time.sleep(0.4)

    write_results(results)
    print_summary(results)


if __name__ == "__main__":
    main()
