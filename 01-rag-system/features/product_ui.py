from __future__ import annotations

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
                <span class="brand-chip brand-chip-muted">OpenAI • Fine-Tuned • Auto</span>
            </div>
            <div style="font-size:2.4rem;font-weight:800;line-height:1.08;margin-bottom:0.45rem;">
                &#127758; Banking &amp; Finance Copilot
            </div>
            <div class="copilot-subtitle">
                Grounded AI assistant for banking and financial knowledge.
            </div>
            <div class="hero-note">
                Retrieval-first answers, transparent source grounding, and a cleaner copilot workflow for banking and compliance questions.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_summary(base_doc_count: int, upload_doc_count: int, upload_chunk_count: int) -> None:
    st.markdown("### Accessibility Summary")
    st.caption(
        "Large text improves readability, high contrast strengthens visual separation, and simplified display shortens answer formatting while keeping sources separate."
    )
    st.markdown("### Copilot Scope")
    st.markdown("- Grounded retrieval from embedded banking knowledge")
    st.markdown("- Session-friendly document uploads")
    st.markdown("- OpenAI, Fine-Tuned, and Auto model modes")
    st.markdown("- Preview voice input and working answer read-aloud")
    st.caption(f"Base knowledge files: {base_doc_count}")
    st.caption(f"Uploaded documents: {upload_doc_count}")
    st.caption(f"Uploaded chunks: {upload_chunk_count}")


def render_metrics(messages: list[dict]) -> None:
    assistant_messages = [message for message in messages if message["role"] == "assistant"]
    avg_latency = round(mean(message["latency_ms"] for message in assistant_messages)) if assistant_messages else 0
    avg_chunks = round(mean(message["retrieved_chunks"] for message in assistant_messages), 1) if assistant_messages else 0
    avg_sources = round(mean(len(message["sources"]) for message in assistant_messages), 1) if assistant_messages else 0
    fallback_count = sum(1 for message in assistant_messages if message.get("confidence") == "Low")
    stats = [
        ("Session Answers", len(assistant_messages)),
        ("Avg Latency", f"{avg_latency} ms"),
        ("Avg Retrieved Chunks", avg_chunks),
        ("Avg Sources / Answer", avg_sources),
        ("Low-Confidence Responses", fallback_count),
    ]
    columns = st.columns(len(stats))
    for column, (label, value) in zip(columns, stats):
        column.markdown(
            f"""
            <div class="stat-card">
                <div class="stat-label">{label}</div>
                <div class="stat-value">{value}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_empty_state() -> None:
    st.markdown(
        """
        <div class="welcome-card">
            <div style="font-weight:700;margin-bottom:0.45rem;font-size:1.05rem;">Ready when you are</div>
            <div style="color:#475569;line-height:1.7;">
                Ask a banking question, upload a policy document, or use Voice Input (Preview). The copilot will answer from retrieved evidence first and keep the supporting sources separate from the main response.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption("Suggested prompts: Compare AML and KYC, explain Basel III, ask about FDIC coverage, or test an uploaded policy document.")


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
                <div style="display:flex;justify-content:space-between;gap:0.75rem;align-items:center;margin-bottom:0.25rem;">
                    <div style="font-weight:700;">Source {card['rank']}: {card['label']}</div>
                    <div style="font-size:0.76rem;color:#64748b;text-transform:uppercase;letter-spacing:0.04em;">{card['source_type']}</div>
                </div>
                <div style="color:#334155;line-height:1.6;">{card['preview']}</div>
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

    st.markdown("<div class='answer-shell'>", unsafe_allow_html=True)
    st.markdown(answer)
    st.markdown(
        " ".join(
            [
                f"<span class='meta-pill'>Model: {message['backend']}</span>",
                f"<span class='meta-pill'>Response time: {message['latency_ms']} ms</span>",
                f"<span class='meta-pill'>Retrieved chunks: {message['retrieved_chunks']}</span>",
                f"<span class='meta-pill'>Confidence: {message['confidence']}</span>",
            ]
        ),
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

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

    render_voice_output(message["answer"], message_key)


def render_footer() -> None:
    st.markdown(
        """
        <div class="copilot-footer">
            <div class="copilot-footer-note">
                AI-generated responses can make mistakes. Verify important banking, compliance, legal, or regulatory details with official sources. Never share card numbers, account credentials, or sensitive personal data in chat.
            </div>
            <div class="copilot-footer-meta">
                <span>Built by <strong>Rakesh Madasani</strong></span>
                <span class="footer-divider">•</span>
                <a href="https://www.linkedin.com/in/rakesh-madasani-b217b71b0/" target="_blank">LinkedIn</a>
                <span class="footer-divider">•</span>
                <a href="https://github.com/rakeshmadasaniai/banking-genai-portfolio" target="_blank">GitHub</a>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
