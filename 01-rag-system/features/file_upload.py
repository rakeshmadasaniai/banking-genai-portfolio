from __future__ import annotations

import streamlit as st

from core.retriever import update_uploaded_index_state


def render_document_uploads() -> list:
    uploaded_docs = st.file_uploader(
        "Upload banking documents",
        type=["pdf", "docx", "txt"],
        accept_multiple_files=True,
        help="Uploaded files are indexed for the current session and searched alongside the embedded banking knowledge base.",
    )
    update_uploaded_index_state(uploaded_docs)
    return uploaded_docs or []


def render_image_uploads() -> list:
    uploaded_images = st.file_uploader(
        "Upload images (experimental)",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True,
        help="Image upload is prepared for future OCR or vision support. For now, images are previewed but not used in retrieval.",
    )
    if uploaded_images:
        st.caption("Image understanding is currently a placeholder. Uploaded images are shown for workflow completeness.")
    return uploaded_images or []
