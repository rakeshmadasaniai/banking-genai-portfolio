from app.backends import (
    COMPARISON_RAG_PROMPT,
    RAG_PROMPT,
    confidence_label,
    extractive_answer,
    format_history,
    get_backend,
    is_comparison_query,
    is_simple_factual_query,
)
from app.config import FALLBACK_ANSWER
from app.retriever import boosted_context, build_context, retrieve_context_once, source_label


def generate_with_shared_retrieval(
    question: str,
    history: list[dict[str, str]] | None = None,
    backend_name: str | None = None,
) -> dict:
    history = history or []
    context_docs = retrieve_context_once(question)
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
        prompt_text = prompt_template.format(
            history=format_history(history),
            context=context,
            question=question,
        )
        answer = get_backend(backend_name).invoke(prompt_text)

    return {
        "backend": backend_name or "openai",
        "response": answer,
        "sources": unique_sources,
        "confidence": confidence_label(len(unique_sources), answer_text=answer, extractive=used_extractive_path),
        "history_used": bool(history),
        "shared_retrieval": True,
    }
