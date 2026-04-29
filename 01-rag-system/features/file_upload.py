from __future__ import annotations

import streamlit as st

from core.retriever import update_uploaded_index_state


def render_document_uploads() -> list:
    uploaded_docs = st.file_uploader(
        "Upload documents",
        type=["pdf", "docx", "txt"],
        accept_multiple_files=True,
        help=None,
    )
    update_uploaded_index_state(uploaded_docs)
    st.caption("PDF | DOCX | TXT")
    return uploaded_docs or []


def render_image_uploads() -> list:
    uploaded_images = st.file_uploader(
        "Image Upload",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True,
        help=None,
    )
    st.session_state.uploaded_images = uploaded_images or []
    if uploaded_images:
        st.caption(f"{len(uploaded_images)} image file(s) attached")
    return uploaded_images or []
