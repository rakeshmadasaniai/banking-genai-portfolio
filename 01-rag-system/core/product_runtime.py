from __future__ import annotations

import html
import time
from typing import Any

import streamlit as st

from core.retriever import get_base_index, load_base_documents, retrieve_shared_context
from features.accessibility import apply_accessibility_styles, render_accessibility_controls
from features.file_upload import render_document_uploads, render_image_uploads
from features.product_ui import (
    render_about_section,
    render_assistant_message,
    render_footer,
    render_header,
    render_safety_notice,
    render_session_insights,
    render_sidebar_summary,
    render_stack_section,
    render_starter_prompts,
    render_user_message,
    render_welcome_card,
)
from features.voice_controls import render_voice_input_preview
from models.auto_router import run_auto_mode
from models.finetuned_mode import generate_finetuned_response
from models.openai_mode import generate_openai_response


MODEL_DESCRIPTIONS = {
    "OpenAI": "Most stable live mode for grounded financial answers.",
    "Fine-Tuned": "Domain-adapted banking model path for specialized tone and phrasing.",
    "Auto": "Selects the strongest grounded answer across available model paths.",
}


def _chat_title(messages: list[dict[str, Any]]) -> str:
    for message in messages:
        if message.get("role") == "user" and message.get("content"):
            title = " ".join(str(message["content"]).split())
            return title[:42] + ("..." if len(title) > 42 else "")
    return "New chat"


def _get_active_chat() -> dict[str, Any]:
    chat_id = st.session_state.active_chat_id
    for chat in st.session_state.chat_threads:
        if chat["id"] == chat_id:
            return chat
    fallback = st.session_state.chat_threads[0]
    st.session_state.active_chat_id = fallback["id"]
    return fallback


def _save_active_chat() -> None:
    active_chat = _get_active_chat()
    active_chat["messages"] = [dict(message) for message in st.session_state.messages]
    active_chat["title"] = _chat_title(active_chat["messages"])


def _load_active_chat() -> None:
    st.session_state.messages = [dict(message) for message in _get_active_chat()["messages"]]


def _create_new_chat() -> None:
    _save_active_chat()
    new_id = f"chat-{int(time.time() * 1000)}"
    st.session_state.chat_threads.insert(0, {"id": new_id, "title": "New chat", "messages": []})
    st.session_state.active_chat_id = new_id
    st.session_state.messages = []


def _ensure_chat_state() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "chat_threads" not in st.session_state:
        initial_messages = [dict(message) for message in st.session_state.messages]
        st.session_state.chat_threads = [{"id": "chat-1", "title": _chat_title(initial_messages), "messages": initial_messages}]
        st.session_state.active_chat_id = "chat-1"
    elif "active_chat_id" not in st.session_state:
        st.session_state.active_chat_id = st.session_state.chat_threads[0]["id"]
    _load_active_chat()


def _stream_answer_preview(answer: str) -> None:
    words = answer.split()
    placeholder = st.empty()
    placeholder.markdown("<div class='thinking-line'>Thinking...</div>", unsafe_allow_html=True)
    time.sleep(0.2)
    if not words:
        placeholder.empty()
        return
    partial_words: list[str] = []
    for index, word in enumerate(words):
        partial_words.append(word)
        suffix = " <span class='typing-cursor'>|</span>" if index < len(words) - 1 else ""
        placeholder.markdown(
            f"<div class='answer-shell'>{html.escape(' '.join(partial_words))}{suffix}</div>",
            unsafe_allow_html=True,
        )
        time.sleep(0.012 if index < 60 else 0.004)
    placeholder.empty()


def _run_selected_model(question: str, retrieval: dict, model_mode: str) -> dict:
    if model_mode == "OpenAI":
        return generate_openai_response(question, retrieval)
    if model_mode == "Fine-Tuned":
        return generate_finetuned_response(question, retrieval)
    return run_auto_mode(question, retrieval)


def run_product_runtime() -> None:
    st.set_page_config(page_title="Banking & Finance Copilot", page_icon=":earth_africa:", layout="wide", initial_sidebar_state="expanded")

    _ensure_chat_state()

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

    show_source_cards = True
    show_auto_comparison = False
    voice_transcript = ""
    voice_enabled = False

    base_index = get_base_index()
    base_doc_count = len(load_base_documents())

    with st.sidebar:
        st.markdown(
            """
            <div class="sidebar-brand">
                <div class="sidebar-title">&#127757; Banking &amp; Finance Copilot</div>
                <div class="sidebar-subtitle">by Rakesh Madasani</div>
                <div class="sidebar-caption">Grounded banking AI</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button("+ New Chat", use_container_width=True):
            _create_new_chat()
            st.rerun()

        chat_ids = [chat["id"] for chat in st.session_state.chat_threads]
        active_index = chat_ids.index(st.session_state.active_chat_id) if st.session_state.active_chat_id in chat_ids else 0
        selected_chat_id = st.radio(
            "Chat history",
            options=chat_ids,
            index=active_index,
            label_visibility="collapsed",
            format_func=lambda chat_id: next(chat["title"] for chat in st.session_state.chat_threads if chat["id"] == chat_id),
            key="chat_history_selector",
        )
        if selected_chat_id != st.session_state.active_chat_id:
            _save_active_chat()
            st.session_state.active_chat_id = selected_chat_id
            _load_active_chat()
            st.rerun()

        with st.expander("Workspace", expanded=False):
            model_mode = st.radio(
                "Model mode",
                ["OpenAI", "Fine-Tuned", "Auto"],
                index=["OpenAI", "Fine-Tuned", "Auto"].index(st.session_state.model_mode),
                horizontal=True,
                label_visibility="collapsed",
                key="model_mode_selector",
            )
            st.session_state.model_mode = model_mode
            st.caption(MODEL_DESCRIPTIONS[model_mode])
            accessibility = render_accessibility_controls()
            show_source_cards = st.toggle("Detailed source cards", value=True)
            show_auto_comparison = st.toggle("Auto mode comparison", value=False)
            image_files = render_image_uploads()
            if image_files:
                for image in image_files[:2]:
                    st.image(image, caption=image.name, use_container_width=True)
            render_sidebar_summary(base_doc_count, st.session_state.upload_doc_count, st.session_state.upload_chunk_count)
            render_session_insights(st.session_state.messages)

        st.markdown(
            """
            <div class="sidebar-bottom">
                <div class="sidebar-links">
                    <a href="https://github.com/rakeshmadasaniai/banking-genai-portfolio" target="_blank">GitHub</a>
                    <a href="https://www.linkedin.com/in/rakesh-madasani-b217b71b0/" target="_blank">LinkedIn</a>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    apply_accessibility_styles(accessibility)
    render_header()

    if not st.session_state.messages:
        render_welcome_card()
        starter_prompt = render_starter_prompts()
        render_about_section()
        render_stack_section()
    else:
        starter_prompt = None

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

    st.markdown("<div class='composer-shell'>", unsafe_allow_html=True)
    question = st.chat_input("Ask about AML, KYC, FDIC, Basel III, or upload a document...")
    st.markdown("<div class='composer-tools'>", unsafe_allow_html=True)
    composer_cols = st.columns([0.75, 0.8, 1.2, 4.25])
    with composer_cols[0]:
        st.markdown("<div class='composer-control'>", unsafe_allow_html=True)
        with st.popover("＋", use_container_width=True):
            render_document_uploads()
        st.markdown("</div>", unsafe_allow_html=True)
    with composer_cols[1]:
        mic_class = "composer-control mic-control mic-live" if voice_enabled else "composer-control mic-control"
        st.markdown(f"<div class='{mic_class}'>", unsafe_allow_html=True)
        with st.popover("Mic", use_container_width=True):
            voice_transcript, voice_enabled = render_voice_input_preview()
        st.markdown("</div>", unsafe_allow_html=True)
    with composer_cols[2]:
        st.markdown(f"<div class='composer-badge'>{st.session_state.model_mode}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    if not question and voice_transcript:
        question = voice_transcript
    if not question and starter_prompt:
        question = starter_prompt

    if not question:
        render_footer()
        render_safety_notice()
        return

    st.session_state.messages.append({"role": "user", "content": question})
    _save_active_chat()
    with st.chat_message("user"):
        render_user_message(question)

    retrieval = retrieve_shared_context(question, base_index, st.session_state.upload_index)
    result = _run_selected_model(question, retrieval, st.session_state.model_mode)

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
        "route_reason": result.get("route_reason"),
        "selection_reason": result.get("selection_reason"),
        "candidate_scores": result.get("candidate_scores"),
        "retrieval_note": (
            "The retriever found weak supporting context for this question. The answer may be incomplete. Try uploading a more relevant document or asking a narrower follow-up."
            if retrieval["weak_retrieval"]
            else ""
        ),
    }
    st.session_state.messages.append(assistant_message)
    _save_active_chat()

    with st.chat_message("assistant"):
        _stream_answer_preview(assistant_message["answer"])
        render_assistant_message(
            assistant_message,
            message_key=f"latest-{len(st.session_state.messages)}",
            simplified_answers=accessibility.simplified_answers,
            show_source_cards=show_source_cards,
            show_auto_comparison=show_auto_comparison,
        )

    render_footer()
    render_safety_notice()

