from __future__ import annotations

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
            <div style="font-size:2.2rem;font-weight:800;line-height:1.1;margin-bottom:0.5rem;">
                🌎 Banking &amp; Finance Copilot
            </div>
            <div class="copilot-subtitle">
                A grounded banking and finance AI assistant for compliance, regulation, risk, and customer-support workflows across U.S. and India banking domains.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_summary(base_doc_count: int, upload_doc_count: int, upload_chunk_count: int) -> None:
    st.markdown("### Copilot Scope")
    st.markdown("- Grounded retrieval from embedded banking knowledge")
    st.markdown("- Session-friendly uploaded document search")
    st.markdown("- OpenAI, fine-tuned, and auto model modes")
    st.markdown("- Accessibility and voice-ready hooks")
    st.caption(f"Base knowledge files: {base_doc_count}")
    st.caption(f"Uploaded documents: {upload_doc_count}")
    st.caption(f"Uploaded chunks: {upload_chunk_count}")


def render_metrics(messages: list[dict]) -> None:
    assistant_messages = [message for message in messages if message["role"] == "assistant"]
    if not assistant_messages:
        avg_latency = 0
        avg_chunks = 0
        avg_sources = 0
    else:
        avg_latency = round(mean(message["latency_ms"] for message in assistant_messages))
        avg_chunks = round(mean(message["retrieved_chunks"] for message in assistant_messages), 1)
        avg_sources = round(mean(len(message["sources"]) for message in assistant_messages), 1)

    col1, col2, col3 = st.columns(3)
    col1.metric("Session Answers", len(assistant_messages))
    col2.metric("Avg Latency", f"{avg_latency} ms")
    col3.metric("Avg Retrieved Chunks", avg_chunks)

    col4, col5 = st.columns(2)
    col4.metric("Avg Sources / Answer", avg_sources)
    col5.metric("Grounded Fallbacks Avoided", sum(1 for msg in assistant_messages if msg["confidence"] != "Low"))


def render_source_cards(source_cards: list[dict]) -> None:
    for card in source_cards:
        st.markdown(
            f"""
            <div class="source-card">
                <div style="font-weight:700;margin-bottom:0.35rem;">{card['label']}</div>
                <div style="color:#475569;line-height:1.55;">{card['preview']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_assistant_message(message: dict, voice_enabled: bool, simplified_answers: bool) -> None:
    answer = message["answer"].replace("\n\n", "\n") if simplified_answers else message["answer"]
    st.markdown(answer)
    st.markdown(
        " ".join(
            [
                f"<span class='meta-pill'>Model: {message['backend']}</span>",
                f"<span class='meta-pill'>Latency: {message['latency_ms']} ms</span>",
                f"<span class='meta-pill'>Chunks: {message['retrieved_chunks']}</span>",
                f"<span class='meta-pill'>Confidence: {message['confidence']}</span>",
            ]
        ),
        unsafe_allow_html=True,
    )
    with st.expander("Sources and grounding", expanded=True):
        render_source_cards(message["source_cards"])
    if message.get("comparison"):
        with st.expander("Auto mode comparison details", expanded=False):
            for label, candidate in message["comparison"].items():
                st.markdown(f"**{label.title()} candidate**")
                st.write(candidate["answer"])
                st.caption(
                    f"Score={candidate['score']['total']} | Groundedness={candidate['score']['groundedness']} | "
                    f"Completeness={candidate['score']['completeness']} | Latency={candidate['latency_ms']} ms"
                )
    render_voice_output(message["answer"], voice_enabled)
