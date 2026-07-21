from __future__ import annotations

from dataclasses import replace
from typing import Any


def _copy_doc(doc: Any, text: str, index: int) -> Any:
    metadata = dict(getattr(doc, "metadata", {}) or {})
    metadata["chunk"] = index
    try:
        return replace(doc, page_content=text, metadata=metadata)
    except Exception:
        from core.retriever import Document

        return Document(page_content=text, metadata=metadata)


def split_documents(documents: list, chunk_size: int = 500, chunk_overlap: int = 90) -> list:
    """Fast local text splitter used on the live Space startup path."""

    chunks = []
    step = max(chunk_size - chunk_overlap, 1)
    for doc in documents:
        text = str(getattr(doc, "page_content", "") or "").strip()
        if not text:
            continue
        if len(text) <= chunk_size:
            chunks.append(_copy_doc(doc, text, 1))
            continue
        chunk_index = 1
        for start in range(0, len(text), step):
            piece = text[start : start + chunk_size].strip()
            if piece:
                chunks.append(_copy_doc(doc, piece, chunk_index))
                chunk_index += 1
            if start + chunk_size >= len(text):
                break
    return chunks
