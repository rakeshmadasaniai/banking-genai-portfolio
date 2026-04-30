from __future__ import annotations

import time
from typing import Any

import streamlit as st

from core.retriever import get_base_index, load_base_documents, retrieve_shared_context
from features.accessibility import apply_accessibility_styles, render_accessibility_controls
from features.file_upload import render_document_uploads, render_image_uploads
from features.product_ui import (
    enforce_composer_pin,
    inject_premium_css,
    render_about_section,
    render_assistant_message,
    render_assistant_thinking,
    render_footer,
    render_header,
    render_session_insights,
    render_sidebar_brand,
    render_sidebar_summary,
    render_stack_section,
    render_starter_prompts,
    render_user_message,
    render_welcome_card,
)
from features.voice_controls import render_voice_input_preview
from models.auto_router import run_auto_mode
from models.autonomous_agent import run_autonomous_agent
from models.finetuned_mode import generate_finetuned_response
from models.openai_mode import generate_openai_response

MODEL_MODES = ["OpenAI", "Fine-Tuned", "Auto", "Autonomous Agent"]

MODEL_DESCRIPTIONS = {
    "OpenAI": "Most stable live mode for grounded financial answers.",
    "Fine-Tuned": "Domain-adapted banking model path for specialized tone and phrasing.",
    "Auto": "Selects the strongest grounded answer across available model paths.",
    "Autonomous Agent": "Plans, executes tools, analyzes evidence, self-checks, and answers with an agent trace.",
}


def _chat_title(messages: list[dict[str, Any]]) -> str:
    for message in messages:
        if message.get("role") == "user" and message.get("content"):
            title = " ".join(str(message["content"]).split())
            return title[:42] + ("..." if len(title) > 42 else "")
    return "New chat"


def _get_active_chat() -> dict[str, Any]:
    for chat in st.session_state.chat_threads:
        if chat["id"] == st.session_state.active_chat_id:
            return chat
    fallback = st.session_state.chat_threads[0]
    st.session_state.active_chat_id = fallback["id"]
    return fallback


def _save_active_chat() -> None:
    chat = _get_active_chat()
    chat["messages"] = [dict(m) for m in st.session_state.messages]
    chat["title"] = _chat_title(chat["messages"])


def _load_active_chat() -> None:
    st.session_state.messages = [dict(m) for m in _get_active_chat()["messages"]]


def _create_new_chat() -> None:
    _save_active_chat()
    new_id = f"chat-{int(time.time() * 1000)}"
    st.session_state.chat_threads.insert(0, {"id": new_id, "title": "New chat", "messages": []})
    st.session_state.active_chat_id = new_id
    st.session_state.messages = []


def _ensure_state() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "chat_threads" not in st.session_state:
        initial = [dict(m) for m in st.session_state.messages]
        st.session_state.chat_threads = [{"id": "chat-1", "title": _chat_title(initial), "messages": initial}]
        st.session_state.active_chat_id = "chat-1"
    elif "active_chat_id" not in st.session_state:
        st.session_state.active_chat_id = st.session_state.chat_threads[0]["id"]
    _load_active_chat()

    defaults = {
        "upload_signature": "",
        "upload_index": None,
        "upload_doc_count": 0,
        "upload_chunk_count": 0,
        "uploaded_images": [],
        "model_mode": "OpenAI",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def _llm_text_call(prompt: str, retrieval: dict) -> str:
    result = generate_openai_response(prompt, retrieval, uploaded_images=[])
    return result.get("answer", "")


def _run_selected_model(question: str, retrieval: dict, mode: str) -> dict:
    images = st.session_state.get("uploaded_images", [])
    if mode == "OpenAI":
        return generate_openai_response(question, retrieval, uploaded_images=images)
    if mode == "Fine-Tuned":
        return generate_finetuned_response(question, retrieval, uploaded_images=images)
    if mode == "Autonomous Agent":
        if "agent_memory" not in st.session_state:
            st.session_state.agent_memory = []
        result = run_autonomous_agent(
            question=question,
            retrieval=retrieval,
            llm_call=lambda p: _llm_text_call(p, retrieval),
            memory=st.session_state.agent_memory,
        )
        st.session_state.agent_memory.append({"question": question, "steps": result.get("agent_steps", [])})
        return result
    return run_auto_mode(question, retrieval, uploaded_images=images)


def run_product_runtime() -> None:
    st.set_page_config(page_title="Banking & Finance Copilot", page_icon="🌍", layout="wide", initial_sidebar_state="expanded")
    _ensure_state()

    inject_premium_css()

    base_index = get_base_index()
    base_doc_count = len(load_base_documents())

    show_source_cards = True
    show_auto_comparison = False
    voice_transcript = ""
    question = ""
    submitted = False

    with st.sidebar:
        st.markdown('<div class="custom-sidebar-anchor"></div>', unsafe_allow_html=True)
        render_sidebar_brand()

        if st.button("+ New Chat", use_container_width=True, key="new_chat_btn"):
            _create_new_chat()
            st.rerun()

        st.markdown('<div class="sidebar-section-label">Recent Chats</div>', unsafe_allow_html=True)
        chat_ids = [c["id"] for c in st.session_state.chat_threads]
        active_index = chat_ids.index(st.session_state.active_chat_id) if st.session_state.active_chat_id in chat_ids else 0
        selected_id = st.radio(
            "Chat history",
            options=chat_ids,
            index=active_index,
            label_visibility="collapsed",
            format_func=lambda cid: next(c["title"] for c in st.session_state.chat_threads if c["id"] == cid),
            key="chat_history_selector",
        )
        if selected_id != st.session_state.active_chat_id:
            _save_active_chat()
            st.session_state.active_chat_id = selected_id
            _load_active_chat()
            st.rerun()

        with st.expander("Workspace", expanded=True):
            mode = st.radio(
                "Model mode",
                MODEL_MODES,
                index=MODEL_MODES.index(st.session_state.model_mode),
                horizontal=True,
                label_visibility="collapsed",
                key="model_mode_selector",
            )
            st.session_state.model_mode = mode
            st.caption(MODEL_DESCRIPTIONS[mode])
            accessibility = render_accessibility_controls()
            show_source_cards = st.toggle("Show source cards", value=False)
            show_auto_comparison = st.toggle("Auto mode comparison", value=False)
            st.markdown('<div class="sidebar-section-label">Knowledge State</div>', unsafe_allow_html=True)
            render_sidebar_summary(base_doc_count, st.session_state.upload_doc_count, st.session_state.upload_chunk_count)
            st.markdown('<div class="sidebar-section-label">Session Metrics</div>', unsafe_allow_html=True)
            render_session_insights(st.session_state.messages)

    apply_accessibility_styles(accessibility)

    render_header()

    if not st.session_state.messages:
        render_welcome_card()
        starter_prompt = render_starter_prompts()
        render_about_section()
        render_stack_section()
    else:
        starter_prompt = None

    for i, msg in enumerate(st.session_state.messages):
        if msg.get("role") == "user":
            render_user_message(str(msg.get("content", "")))
        else:
            render_assistant_message(
                msg,
                message_key=f"history-{i}",
                simplified_answers=accessibility.simplified_answers,
                show_source_cards=show_source_cards,
                show_auto_comparison=show_auto_comparison,
            )

    with st.form("composer_form", clear_on_submit=True, border=False):
        st.markdown("<div class='composer-marker'></div>", unsafe_allow_html=True)
        st.markdown("<div class='composer-row'>", unsafe_allow_html=True)
        c1, c2, c3, c4, c5 = st.columns([0.95, 1.25, 4.0, 1.0, 0.7])
        with c1:
            with st.popover("+", use_container_width=True):
                render_document_uploads()
                render_image_uploads()
        with c2:
            mode = st.selectbox(
                "Composer model",
                MODEL_MODES,
                index=MODEL_MODES.index(st.session_state.model_mode),
                label_visibility="collapsed",
                key="composer_model_mode",
            )
            st.session_state.model_mode = mode
        with c3:
            question = st.text_input(
                "Ask banking question",
                placeholder="Ask anything about banking, finance, regulations, or compliance...",
                label_visibility="collapsed",
                key="composer_text_input_inline",
            )
        with c4:
            with st.popover("🎤", use_container_width=True):
                voice_transcript, _ = render_voice_input_preview()
        with c5:
            submitted = st.form_submit_button("↑", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    enforce_composer_pin()

    if not submitted and not voice_transcript and not starter_prompt:
        render_footer()
        return

    if not question and voice_transcript:
        question = voice_transcript
    if not question and starter_prompt:
        question = starter_prompt
    if not question:
        render_footer()
        return

    st.session_state.messages.append({"role": "user", "content": question})
    _save_active_chat()
    render_user_message(question)
    render_assistant_thinking()

    retrieval = retrieve_shared_context(question, base_index, st.session_state.upload_index)
    result = _run_selected_model(question, retrieval, st.session_state.model_mode)

    assistant_msg = {
        "role": "assistant",
        "answer": result.get("answer", ""),
        "backend": result.get("backend", st.session_state.model_mode),
        "latency_ms": result.get("latency_ms", 0),
        "retrieved_chunks": retrieval.get("retrieved_chunks", 0),
        "sources": retrieval.get("sources", []),
        "source_cards": retrieval.get("source_cards", []),
        "confidence": result.get("confidence", "Moderate"),
        "comparison": result.get("comparison"),
        "route_reason": result.get("route_reason"),
        "selection_reason": result.get("selection_reason"),
        "candidate_scores": result.get("candidate_scores"),
        "agent_steps": result.get("agent_steps"),
        "agent_observations": result.get("agent_observations"),
        "voice_lang_hint": result.get("language", ""),
    }
    st.session_state.messages.append(assistant_msg)
    _save_active_chat()

    st.rerun()
