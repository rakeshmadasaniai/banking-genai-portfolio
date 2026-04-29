from __future__ import annotations

import html
import re
from statistics import mean

import streamlit as st

from features.voice_output import render_voice_output

STARTER_PROMPTS = [
    "English: What are the main KYC requirements for banks?",
    "తెలుగు: బ్యాంకుల్లో KYC కోసం అవసరమైన ప్రధాన పత్రాలు ఏమిటి?",
    "中文: 银行KYC合规最重要的要求是什么?",
    "Español: ¿Cuáles son los requisitos principales de KYC para bancos?",
    "Français : Quelles sont les principales exigences KYC pour les banques ?",
    "Русский: Каковы основные требования KYC для банков?",
]


def _as_html_text(text: str) -> str:
    return html.escape(text).replace("\n", "<br>")


def render_header() -> None:
    st.markdown(
        """
        <div class="hero-wrap">
            <div class="brand-row brand-row-centered">
                <span class="brand-chip grounded-chip">Grounded Banking AI</span>
                <span class="brand-chip brand-chip-muted">OpenAI · Fine-Tuned · Auto · Autonomous Agent</span>
            </div>
            <h1 class="hero-title">&#127757; Banking &amp; Finance Copilot</h1>
            <div class="hero-tagline">Grounded AI for banking, compliance, and financial intelligence.</div>
            <div class="hero-oneliner">AI assistant for banking and financial questions with trusted, source-backed answers</div>
            <div class="hero-description">This app helps you understand banking, compliance, and financial rules using verified documents. It gives clear explanations, shows supporting sources, and helps you explore financial topics safely and quickly.</div>
            <div class="hero-divider"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_welcome_card() -> None:
    st.markdown(
        """
        <div class="answer-shell welcome-card">
            <div class="welcome-title">Hi, I'm your &#127757; Banking &amp; Finance Copilot.</div>
            <div class="welcome-copy">
                I provide clear, source-backed answers for AML and KYC, FDIC and Basel III, RBI guidance, and financial regulations.
                You can also upload documents for contextual answers. I'll always show where each answer comes from.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_starter_prompts() -> str | None:
    st.markdown('<div class="starter-label">Popular prompts</div>', unsafe_allow_html=True)
    cols = st.columns(3)
    selected = None
    for index, prompt in enumerate(STARTER_PROMPTS):
        with cols[index % 3]:
            if st.button(prompt, key=f"starter-{index}", use_container_width=True):
                selected = prompt
    return selected


def render_about_section() -> None:
    with st.expander("About this Copilot", expanded=False):
        st.markdown(
            """
🌍 **Banking & Finance Copilot** is a grounded generative AI assistant for banking, compliance, and financial knowledge retrieval.

It uses retrieval-augmented generation (RAG) to answer questions using trusted documents such as regulatory guidelines, KYC rules, AML policies, and financial standards.

The system supports multiple intelligence modes including OpenAI, fine-tuned models, auto-routing, and autonomous agentic reasoning.
            """
        )


def render_stack_section() -> None:
    with st.expander("Tech Stack & Features", expanded=False):
        st.markdown(
            """
**Tech Stack**
- Python
- Streamlit
- OpenAI API
- Hugging Face
- FAISS / vector search
- LangChain / custom RAG
- QLoRA fine-tuning
- Speech-to-text / text-to-speech

**Key Features**
- Grounded answers with source citations
- OpenAI / Fine-Tuned / Auto / Autonomous Agent modes
- Multi-chat history
- Document and image input support
- Voice interaction
            """
        )


def render_sidebar_summary(base_doc_count: int, upload_doc_count: int, upload_chunk_count: int) -> None:
    st.caption(f"Base files: **{base_doc_count}**")
    st.caption(f"Uploaded docs: **{upload_doc_count}**")
    st.caption(f"Uploaded chunks: **{upload_chunk_count}**")


def render_session_insights(messages: list[dict]) -> None:
    assistant_messages = [message for message in messages if message["role"] == "assistant"]
    avg_latency = round(mean(message["latency_ms"] for message in assistant_messages)) if assistant_messages else 0
    avg_chunks = round(mean(message["retrieved_chunks"] for message in assistant_messages), 1) if assistant_messages else 0
    st.markdown(
        f"""
        <div class="session-panel">
            <div class="session-item"><span>Answers</span><strong>{len(assistant_messages)}</strong></div>
            <div class="session-item"><span>Avg latency</span><strong>{avg_latency} ms</strong></div>
            <div class="session-item"><span>Avg chunks</span><strong>{avg_chunks}</strong></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_user_message(text: str) -> None:
    st.markdown(
        f"""
        <div class="user-row">
            <div class="user-bubble">{_as_html_text(text)}</div>
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
                <div class="source-meta">Chunk {card['rank']}</div>
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
    st.markdown(f"<div class='answer-shell'>{_as_html_text(answer)}</div>", unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="meta-line">
            {html.escape(message['backend'])} | {message['latency_ms']} ms | {message['retrieved_chunks']} chunks | {html.escape(message['confidence'])} confidence
        </div>
        """,
        unsafe_allow_html=True,
    )
    if message.get("retrieval_note"):
        st.markdown(f'<div class="warning-pill">{html.escape(message["retrieval_note"])}</div>', unsafe_allow_html=True)

    action_columns = st.columns([1.2, 1.0, 6.0])
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

    agent_steps = message.get("agent_steps") or []
    agent_observations = message.get("agent_observations") or []
    if agent_steps:
        with st.expander("Autonomous Agent Execution Trace", expanded=False):
            for step in agent_steps:
                st.markdown(
                    f"**Step {step.get('step')} — {str(step.get('action', '')).title()}**\n\n"
                    f"Reason: {step.get('thought', '')}\n\n"
                    f"Input: `{step.get('input', '')}`"
                )
    if agent_observations:
        with st.expander("Tool Observations", expanded=False):
            for obs in agent_observations:
                st.markdown(f"**Tool:** `{obs.get('tool')}`")
                st.write(obs.get("result"))


def render_footer() -> None:
    st.markdown(
        """
        <div class="copilot-footer">
            <div class="footer-inline">
                <div class="rm-avatar">RM</div>
                <span class="footer-name">Rakesh Madasani</span>
                <span class="footer-divider">|</span>
                <a href="https://www.linkedin.com/in/rakesh-madasani-b217b71b0/" target="_blank" aria-label="LinkedIn">LinkedIn</a>
                <span class="footer-divider">|</span>
                <a href="https://github.com/rakeshmadasaniai/banking-genai-portfolio" target="_blank" aria-label="GitHub">GitHub</a>
                <span class="footer-divider">|</span>
                <span class="footer-note">AI can make mistakes. Verify important information with official sources.</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
