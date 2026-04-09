from __future__ import annotations

import html
import re
from statistics import mean

import streamlit as st

from features.voice_output import render_voice_output


def render_header() -> None:
    st.markdown(
        """
        <div class="copilot-hero">
            <div class="brand-row">
                <span class="brand-chip">Grounded Banking AI</span>
                <span class="brand-chip brand-chip-muted">OpenAI &middot; Fine-Tuned &middot; Auto</span>
            </div>
            <div class="hero-title">Banking &amp; Finance Copilot</div>
            <div class="copilot-subtitle">Grounded AI assistant for banking and financial knowledge.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_summary(base_doc_count: int, upload_doc_count: int, upload_chunk_count: int) -> None:
    st.markdown("### Stack")
    st.caption("Streamlit UI, FAISS retrieval, sentence-transformers embeddings, OpenAI, and a Hugging Face fine-tuned path.")

    st.markdown("### Model Modes")
    st.caption("OpenAI is the strongest stable baseline. Fine-Tuned uses the banking-domain model path. Auto compares grounded candidates on shared retrieval.")

    st.markdown("### What This Shows")
    st.caption("A retrieval-grounded copilot for regulated-domain Q&A, uploaded document search, and explainable model routing.")
    st.caption(f"Base knowledge files: {base_doc_count}")
    st.caption(f"Uploaded documents: {upload_doc_count}")
    st.caption(f"Uploaded chunks: {upload_chunk_count}")


def render_session_insights(messages: list[dict]) -> None:
    assistant_messages = [message for message in messages if message["role"] == "assistant"]
    avg_latency = round(mean(message["latency_ms"] for message in assistant_messages)) if assistant_messages else 0
    avg_chunks = round(mean(message["retrieved_chunks"] for message in assistant_messages), 1) if assistant_messages else 0
    avg_sources = round(mean(len(message["sources"]) for message in assistant_messages), 1) if assistant_messages else 0
    fallback_count = sum(1 for message in assistant_messages if message.get("confidence") == "Low")
    st.markdown(
        f"""
        <div class="session-panel">
            <div class="session-item"><span>Answers</span><strong>{len(assistant_messages)}</strong></div>
            <div class="session-item"><span>Avg latency</span><strong>{avg_latency} ms</strong></div>
            <div class="session-item"><span>Avg chunks</span><strong>{avg_chunks}</strong></div>
            <div class="session-item"><span>Avg sources</span><strong>{avg_sources}</strong></div>
            <div class="session-item"><span>Low confidence</span><strong>{fallback_count}</strong></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_example_questions() -> str | None:
    st.markdown('<div class="empty-label">Try asking about</div>', unsafe_allow_html=True)
    prompts = [
        "How does FDIC insurance work and what deposits are covered?",
        "Compare CTR reporting thresholds in the U.S. and India.",
        "Explain Regulation E liability limits for unauthorized transfers.",
        "What is CECL and how does it change expected credit loss accounting?",
        "What documents are required for KYC of an individual in India?",
        "How does uploaded guidance change answers to policy questions?",
    ]
    selected = None
    columns = st.columns(2)
    for index, prompt in enumerate(prompts):
        with columns[index % 2]:
            if st.button(prompt, key=f"chip_{index}", use_container_width=True):
                selected = prompt
    return selected


def render_input_toolbar(model_name: str, mic_active: bool = False) -> None:
    mic_classes = "toolbar-pill toolbar-icon toolbar-mic"
    if mic_active:
        mic_classes += " toolbar-mic-active"
    st.markdown(
        f"""
        <div class="input-toolbar">
            <div class="input-toolbar-left">
                <span class="toolbar-pill toolbar-icon" aria-hidden="true">+</span>
                <span class="{mic_classes}" aria-hidden="true">&#127897;</span>
            </div>
            <div class="input-toolbar-right">
                <span class="model-badge">{html.escape(model_name)}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_user_message(text: str) -> None:
    st.markdown(
        f"""
        <div class="user-row">
            <div class="user-bubble">{html.escape(text)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _simplify_answer(answer: str) -> str:
    text = re.sub(r"^[\-\*\u2022]\s*", "", answer, flags=re.MULTILINE)
    text = re.sub(r"\n{2,}", "\n", text).strip()
    sentences = [segment.strip() for segment in re.split(r"(?<=[.!?])\s+", text) if segment.strip()]
    grouped = []
    for index in range(0, len(sentences), 2):
        grouped.append(" ".join(sentences[index : index + 2]))
    return "\n\n".join(grouped) if grouped else answer


def render_source_cards(source_cards: list[dict]) -> None:
    for card in source_cards:
        st.markdown(
            f"""
            <div class="source-card">
                <div class="source-title">{html.escape(card['label'])}</div>
                <div class="source-meta">Chunk {card['rank']} &middot; {html.escape(card['source_type'])}</div>
                <div class="source-preview">{html.escape(card['preview'])}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_assistant_message(
    message: dict,
    message_key: str,
    simplified_answers: bool,
    show_source_cards: bool,
    show_auto_comparison: bool,
) -> None:
    answer = _simplify_answer(message["answer"]) if simplified_answers else message["answer"]

    if message.get("retrieval_note"):
        st.warning(message["retrieval_note"])

    st.markdown(f"<div class='answer-shell'>{html.escape(answer)}</div>", unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="meta-line">
            {html.escape(message['backend'])} &middot; {round(message['latency_ms'] / 1000, 1)} s &middot; {message['retrieved_chunks']} chunks &middot; {html.escape(message['confidence'])} confidence
        </div>
        """,
        unsafe_allow_html=True,
    )

    action_columns = st.columns([1.4, 1.0, 8])
    with action_columns[0]:
        render_voice_output(message["answer"], message_key)
    with action_columns[1]:
        st.button("Copy", key=f"copy-{message_key}", use_container_width=True)

    if show_source_cards:
        with st.expander("Sources and grounding", expanded=False):
            render_source_cards(message["source_cards"])

    if show_auto_comparison and message.get("comparison"):
        with st.expander("Auto mode comparison", expanded=False):
            for label, candidate in message["comparison"].items():
                st.markdown(f"**{label.title()} candidate**")
                st.write(candidate["answer"])
                st.caption(
                    f"Winner score={candidate['score']['total']} | Groundedness={candidate['score']['groundedness']} | "
                    f"Completeness={candidate['score']['completeness']} | Latency score={candidate['score']['latency']}"
                )


def render_footer() -> None:
    st.markdown(
        """
        <div class="copilot-footer">
            <div class="footer-pill">
                <div class="rm-avatar">RM</div>
                <span class="footer-name">Rakesh Madasani</span>
                <span class="footer-divider">|</span>
                <a href="https://www.linkedin.com/in/rakesh-madasani-b217b71b0/" target="_blank" aria-label="LinkedIn">LinkedIn</a>
                <span class="footer-divider">|</span>
                <a href="https://github.com/rakeshmadasaniai/banking-genai-portfolio" target="_blank" aria-label="GitHub">GitHub</a>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
