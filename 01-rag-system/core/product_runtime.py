from __future__ import annotations

import streamlit as st

from core.retriever import get_base_index, load_base_documents, retrieve_shared_context
from features.accessibility import apply_accessibility_styles, render_accessibility_controls
from features.file_upload import render_document_uploads, render_image_uploads
from features.product_ui import (
    render_assistant_message,
    render_example_questions,
    render_footer,
    render_header,
    render_input_toolbar,
    render_session_insights,
    render_sidebar_summary,
    render_user_message,
)
from features.voice_controls import render_voice_input_preview
from models.auto_router import run_auto_mode
from models.finetuned_mode import generate_finetuned_response
from models.openai_mode import generate_openai_response


def run_product_runtime() -> None:
    st.set_page_config(page_title="Banking & Finance Copilot", page_icon=":bank:", layout="wide", initial_sidebar_state="expanded")

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
    if "model_mode" not in st.session_state:
        st.session_state.model_mode = "OpenAI"

    base_index = get_base_index()
    base_doc_count = len(load_base_documents())

    with st.sidebar:
        st.markdown(
            """
            <div class="sidebar-brand">
                <div class="sidebar-title">Banking &amp; Finance Copilot</div>
                <div class="sidebar-subtitle">by Rakesh Madasani</div>
                <div class="sidebar-caption">Grounded banking AI</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("+ New chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

        st.markdown('<div class="sidebar-section-label">Model</div>', unsafe_allow_html=True)
        model_options = ["OpenAI", "Fine-Tuned", "Auto"]
        default_index = model_options.index(st.session_state.model_mode) if st.session_state.model_mode in model_options else 0
        model_mode = st.radio(
            "Model mode",
            model_options,
            index=default_index,
            horizontal=True,
            label_visibility="collapsed",
            key="model_mode_selector",
        )
        st.session_state.model_mode = model_mode
        model_descriptions = {
            "OpenAI": "Strongest stable path for live grounded answers.",
            "Fine-Tuned": "Banking-domain response path for portfolio demos.",
            "Auto": "Retrieves once, compares candidates, and picks the stronger answer.",
        }
        st.caption(model_descriptions[model_mode])

        st.markdown('<div class="sidebar-section-label">Knowledge</div>', unsafe_allow_html=True)
        document_files = render_document_uploads()
        image_files: list = []

        with st.expander("Accessibility & Voice", expanded=False):
            accessibility = render_accessibility_controls()
            voice_transcript, voice_enabled = render_voice_input_preview()

        st.markdown("<div class='sidebar-advanced-spacer'></div>", unsafe_allow_html=True)
        with st.expander("Advanced & Stats", expanded=False):
            show_source_cards = st.toggle(
                "Detailed source cards",
                value=True,
                help="Keep supporting source cards visible beneath each answer.",
            )
            show_auto_comparison = st.toggle(
                "Auto mode comparison",
                value=False,
                help="Reveal how OpenAI and the fine-tuned path were scored when Auto mode chooses a winner.",
            )
            image_files = render_image_uploads()
            if image_files:
                st.markdown("### Image previews")
                for image in image_files[:2]:
                    st.image(image, caption=image.name, use_container_width=True)
            render_sidebar_summary(base_doc_count, st.session_state.upload_doc_count, st.session_state.upload_chunk_count)
            render_session_insights(st.session_state.messages)

    apply_accessibility_styles(accessibility)
    render_header()

    if not st.session_state.messages:
        example_question = render_example_questions()
    else:
        example_question = None

    for index, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            if message["role"] == "user":
                render_user_message(message["content"])
            else:
                render_assistant_message(
                    message,
                    message_key=f"history-{index}",
                    simplified_answers=accessibility.simplified_answers,
                    show_source_cards=show_source_cards,
                    show_auto_comparison=show_auto_comparison,
                )

    render_input_toolbar(model_mode, mic_active=voice_enabled)
    question = st.chat_input("Ask about AML, KYC, FDIC, Basel, RBI guidance, or uploaded documents...")
    if not question and voice_transcript:
        question = voice_transcript
    if not question and example_question:
        question = example_question

    if not question:
        render_footer()
        return

    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        render_user_message(question)

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

