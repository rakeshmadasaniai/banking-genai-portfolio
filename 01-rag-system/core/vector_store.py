from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Any

import streamlit as st
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

from core.utils import keyword_tokens


class KeywordVectorStore:
    """Small fallback retriever that avoids model downloads on CPU-only Spaces."""

    def __init__(self, documents: list[Any]):
        self.documents = documents
        self._indexed = [(doc, keyword_tokens(doc.page_content)) for doc in documents]

    def similarity_search(self, query: str, k: int = 4) -> list[Any]:
        query_terms = keyword_tokens(query)
        if not query_terms:
            return self.documents[:k]

        scored: list[tuple[float, int, Any]] = []
        for position, (doc, doc_terms) in enumerate(self._indexed):
            overlap = len(query_terms & doc_terms)
            coverage = overlap / max(len(query_terms), 1)
            density = overlap / max(len(doc_terms), 1)
            score = coverage * 0.8 + density * 0.2
            if score > 0:
                scored.append((score, -position, doc))

        scored.sort(reverse=True)
        if scored:
            return [doc for _, _, doc in scored[:k]]
        return self.documents[:k]


@dataclass
class VectorIndex:
    vectorstore: Any
    doc_count: int
    chunk_count: int
    origin: str
    backend: str = "keyword"


@st.cache_resource(show_spinner=False)
def get_embeddings(model_name: str) -> HuggingFaceEmbeddings:
    return HuggingFaceEmbeddings(model_name=model_name)


def _build_keyword_index(documents: list, origin: str) -> VectorIndex:
    return VectorIndex(
        vectorstore=KeywordVectorStore(documents),
        doc_count=len({doc.metadata.get("source", "unknown") for doc in documents}),
        chunk_count=len(documents),
        origin=origin,
        backend="keyword",
    )


def build_vector_index(documents: list, embeddings_model_name: str, origin: str) -> VectorIndex | None:
    if not documents:
        return None

    backend = os.environ.get("RAG_RETRIEVAL_BACKEND", "keyword").strip().lower()
    if backend != "faiss":
        return _build_keyword_index(documents, origin)

    try:
        vectorstore = FAISS.from_documents(documents, get_embeddings(embeddings_model_name))
        return VectorIndex(
            vectorstore=vectorstore,
            doc_count=len({doc.metadata.get("source", "unknown") for doc in documents}),
            chunk_count=len(documents),
            origin=origin,
            backend="faiss",
        )
    except Exception as exc:
        st.warning(f"FAISS retrieval could not initialize; using fast keyword retrieval instead. ({exc})")
        return _build_keyword_index(documents, origin)
