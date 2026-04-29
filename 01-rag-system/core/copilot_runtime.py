from __future__ import annotations

import streamlit as st

from core.retriever import get_base_index, load_base_documents, retrieve_shared_context
from features.accessibility import apply_accessibility_styles, render_accessibility_controls
from features.file_upload import render_document_uploads, render_image_uploads
from features.ui_components import render_assistant_message, render_header, render_metrics, render_sidebar_summary
from features.voice_input import render_voice_input
from models.auto_router import run_auto_mode
from models.finetuned_mode import generate_finetuned_response
from models.openai_mode import generate_openai_response


def run_copilot_runtime() -> None:
    st.set_page_config(page_title="🌎 Banking & Finance Copilot", page_icon="🌎", layout="wide")

    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "upload_signature" not in st.session_state:
        st.session_state.upload_signature = ""
    if "upload_index" not in st.session_state:
        st.session_state.upload_index = None
    if "upload_doc_count" not in st.session_state:
        st.session_state.upload_doc_count = 0
    if "upload_chunk_count" not in st.session_state:
        st.session_state.upload_chunk_count = 0

    base_index = get_base_index()
    base_doc_count = len(load_base_documents())

    with st.sidebar:
        st.markdown("## Workspace")
        model_mode = st.selectbox("Model mode", ["OpenAI", "Fine-Tuned", "Auto"], index=0)
        document_files = render_document_uploads()
        image_files = render_image_uploads()
        accessibility = render_accessibility_controls()
        render_sidebar_summary(base_doc_count, st.session_state.upload_doc_count, st.session_state.upload_chunk_count)
        if document_files:
            st.caption("Uploaded documents are ready for session retrieval.")
        if image_files:
            st.markdown("### Uploaded image previews")
            for image in image_files[:2]:
                st.image(image, caption=image.name, use_container_width=True)
        if st.button("Clear chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

    apply_accessibility_styles(accessibility)
    render_header()
    render_metrics(st.session_state.messages)

    st.caption(
        "This copilot keeps answers grounded in retrieved banking material, supports uploaded document search, "
        "and lets you switch between OpenAI, fine-tuned, and auto-selected response modes."
    )

    voice_transcript, voice_used = render_voice_input()

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["role"] == "user":
                st.markdown(message["content"])
            else:
                render_assistant_message(message, voice_used, accessibility.simplified_answers)

    question = st.chat_input("Ask about KYC, AML, RBI guidance, FDIC, Basel, or uploaded documents...")
    if not question and voice_transcript:
        question = voice_transcript

    if not question:
        return

    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    retrieval = retrieve_shared_context(question, base_index, st.session_state.upload_index)

    if model_mode == "OpenAI":
        result = generate_openai_response(question, retrieval)
    elif model_mode == "Fine-Tuned":
        result = generate_finetuned_response(question, retrieval)
    else:
        result = run_auto_mode(question, retrieval)

    assistant_message = {
        "role": "assistant",
        "answer": result["answer"],
        "backend": result["backend"],
        "latency_ms": result["latency_ms"],
        "retrieved_chunks": retrieval["retrieved_chunks"],
        "sources": retrieval["sources"],
        "source_cards": retrieval["source_cards"],
        "confidence": result["confidence"],
        "comparison": result.get("comparison"),
    }
    st.session_state.messages.append(assistant_message)

    with st.chat_message("assistant"):
        render_assistant_message(assistant_message, voice_used, accessibility.simplified_answers)
