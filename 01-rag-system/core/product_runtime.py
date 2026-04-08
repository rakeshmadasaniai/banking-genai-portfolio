from __future__ import annotations

import streamlit as st

from core.retriever import get_base_index, load_base_documents, retrieve_shared_context
from features.accessibility import apply_accessibility_styles, render_accessibility_controls
from features.file_upload import render_document_uploads, render_image_uploads
from features.product_ui import (
    render_assistant_message,
    render_empty_state,
    render_footer,
    render_header,
    render_metrics,
    render_sidebar_summary,
)
from features.voice_controls import render_voice_input_preview
from models.auto_router import run_auto_mode
from models.finetuned_mode import generate_finetuned_response
from models.openai_mode import generate_openai_response


def run_product_runtime() -> None:
    st.set_page_config(page_title="Banking & Finance Copilot", page_icon=":earth_americas:", layout="wide")

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
        st.markdown("### Model Selection")
        model_mode = st.selectbox("Model mode", ["OpenAI", "Fine-Tuned", "Auto"], index=0)
        st.caption("OpenAI is the strongest stable baseline. Auto compares grounded candidates on the same retrieved context.")

        st.markdown("### Knowledge Inputs")
        document_files = render_document_uploads()
        image_files = render_image_uploads()

        st.markdown("### Voice & Accessibility")
        voice_transcript, _voice_used = render_voice_input_preview()
        accessibility = render_accessibility_controls()

        st.markdown("### Response Settings")
        show_source_cards = st.toggle(
            "Show detailed source cards",
            value=True,
            help="Keep supporting source cards visible beneath each answer.",
        )
        show_auto_comparison = st.toggle(
            "Show Auto mode comparison details",
            value=False,
            help="Reveal how OpenAI and the fine-tuned path were scored when Auto mode chooses a winner.",
        )

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

    if not st.session_state.messages:
        render_empty_state()

    for index, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            if message["role"] == "user":
                st.markdown(message["content"])
            else:
                render_assistant_message(
                    message,
                    message_key=f"history-{index}",
                    simplified_answers=accessibility.simplified_answers,
                    show_source_cards=show_source_cards,
                    show_auto_comparison=show_auto_comparison,
                )

    question = st.chat_input("Ask about KYC, AML, RBI guidance, FDIC, Basel, or uploaded documents...")
    if not question and voice_transcript:
        question = voice_transcript

    if not question:
        render_footer()
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
        "retrieval_note": (
            "The retriever found weak supporting context for this question. The answer may be incomplete. Try uploading a more relevant document or asking a narrower follow-up."
            if retrieval["weak_retrieval"]
            else ""
        ),
    }
    st.session_state.messages.append(assistant_message)

    with st.chat_message("assistant"):
        render_assistant_message(
            assistant_message,
            message_key=f"latest-{len(st.session_state.messages)}",
            simplified_answers=accessibility.simplified_answers,
            show_source_cards=show_source_cards,
            show_auto_comparison=show_auto_comparison,
        )

    render_footer()
