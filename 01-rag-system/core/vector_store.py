from __future__ import annotations

from dataclasses import dataclass

import streamlit as st
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS


@dataclass
class VectorIndex:
    vectorstore: FAISS
    doc_count: int
    chunk_count: int
    origin: str


@st.cache_resource(show_spinner=False)
def get_embeddings(model_name: str) -> HuggingFaceEmbeddings:
    return HuggingFaceEmbeddings(model_name=model_name)


def build_vector_index(documents: list, embeddings_model_name: str, origin: str) -> VectorIndex | None:
    if not documents:
        return None
    vectorstore = FAISS.from_documents(documents, get_embeddings(embeddings_model_name))
    return VectorIndex(
        vectorstore=vectorstore,
        doc_count=len({doc.metadata.get("source", "unknown") for doc in documents}),
        chunk_count=len(documents),
        origin=origin,
    )

