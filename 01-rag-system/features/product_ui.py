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
                <span class="brand-chip brand-chip-muted">OpenAI &bull; Fine-Tuned &bull; Auto</span>
            </div>
            <div style="font-size:1.95rem;font-weight:700;line-height:1.08;margin-bottom:0.32rem;color:#1a1a18;">
                Banking &amp; Finance Copilot
            </div>
            <div class="copilot-subtitle">
                Grounded AI assistant for banking and financial knowledge.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_summary(base_doc_count: int, upload_doc_count: int, upload_chunk_count: int) -> None:
    st.markdown("### Copilot Scope")
    st.markdown("- Grounded retrieval from embedded banking knowledge")
    st.markdown("- Session-friendly document uploads")
    st.markdown("- OpenAI, Fine-Tuned, and Auto model modes")
    st.markdown("- Preview voice input and working answer read-aloud")
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
    st.caption("Try asking about")
    examples = [
        "How does FDIC insurance work and what deposits are covered?",
        "Compare CTR reporting thresholds in the U.S. and India.",
        "Explain Regulation E liability limits for unauthorized transfers.",
        "What is CECL and how does it change expected credit loss accounting?",
        "What documents are usually required for KYC of an individual in India?",
        "How does uploaded guidance change the answer to my policy question?",
    ]
    selected = None
    columns = st.columns(2)
    for index, prompt in enumerate(examples):
        column = columns[index % 2]
        if column.button(prompt, key=f"example-{index}", use_container_width=True):
            selected = prompt
    return selected


def render_input_toolbar(model_name: str) -> None:
    st.markdown(
        f"""
        <div class="input-toolbar">
            <div class="input-toolbar-left">
                <span class="toolbar-pill">+</span>
                <span class="toolbar-pill">&#127897;</span>
            </div>
            <div class="input-toolbar-right">
                <span class="model-badge">{model_name}</span>
            </div>
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
        f"""
        <div class="meta-line">
            {message['backend']} &middot; {message['latency_ms']} ms &middot; {message['retrieved_chunks']} chunks &middot; {message['confidence']} confidence
        </div>
        """,
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
            <div class="footer-pill">
                <div class="rm-avatar">RM</div>
                <span class="footer-name">Rakesh Madasani</span>
                <span class="footer-divider">&vert;</span>
                <a href="https://www.linkedin.com/in/rakesh-madasani-b217b71b0/" target="_blank" aria-label="LinkedIn">LinkedIn</a>
                <span class="footer-divider">&vert;</span>
                <a href="https://github.com/rakeshmadasaniai/banking-genai-portfolio" target="_blank" aria-label="GitHub">GitHub</a>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
