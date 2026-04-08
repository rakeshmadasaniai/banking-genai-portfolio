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
        "Image Upload (Preview)",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True,
        help="Preview-only image upload. Images are displayed in the UI, but they are not analyzed for multimodal reasoning in this version.",
    )
    if uploaded_images:
        st.caption("Preview only: uploaded images are shown back to you, but this version does not perform image reasoning.")
    return uploaded_images or []
