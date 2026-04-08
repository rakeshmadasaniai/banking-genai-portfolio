from __future__ import annotations

import re
from statistics import mean

import streamlit as st

from features.voice_output import render_voice_output


def render_header() -> None:
    st.markdown(
        """
        <div class="copilot-hero">
            <div style="font-size:0.82rem;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;color:#0f766e;margin-bottom:0.35rem;">
                Grounded Banking AI
            </div>
            <div style="font-size:2.2rem;font-weight:800;line-height:1.1;margin-bottom:0.35rem;">
                &#127758; Banking &amp; Finance Copilot
            </div>
            <div class="copilot-subtitle">
                Grounded AI assistant for banking and financial knowledge.
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

    row1 = st.columns(3)
    row1[0].metric("Session Answers", len(assistant_messages))
    row1[1].metric("Avg Latency", f"{avg_latency} ms")
    row1[2].metric("Avg Retrieved Chunks", avg_chunks)

    row2 = st.columns(2)
    row2[0].metric("Avg Sources / Answer", avg_sources)
    row2[1].metric("Low-Confidence Responses", fallback_count)


def render_empty_state() -> None:
    st.markdown(
        """
        <div class="source-card">
            <div style="font-weight:700;margin-bottom:0.35rem;">Ready when you are</div>
            <div style="color:#475569;line-height:1.6;">
                Ask a banking question, upload a policy document, or try the Voice Input (Preview) control.  
                The copilot will keep the answer grounded and show the supporting source cards separately.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption("Suggested prompts: Compare AML and KYC, explain Basel III, or ask about uploaded due-diligence guidance.")


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
                <div style="font-weight:700;margin-bottom:0.25rem;">Source {card['rank']}: {card['label']}</div>
                <div style="font-size:0.82rem;color:#475569;margin-bottom:0.35rem;">Type: {card['source_type']}</div>
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

    if show_source_cards:
        with st.expander("Source cards", expanded=True):
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
