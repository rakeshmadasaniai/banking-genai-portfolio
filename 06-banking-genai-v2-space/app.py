import os
import time
import uuid
from statistics import mean

import requests
import streamlit as st


BACKEND_URL = os.environ.get("BANKING_V2_API_URL", "").rstrip("/")
REQUEST_TIMEOUT = int(os.environ.get("BANKING_V2_TIMEOUT", "60"))


def ensure_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())


def clear_conversation():
    st.session_state.messages = []
    st.session_state.session_id = str(uuid.uuid4())


def call_backend(message: str, compare_mode: bool, use_memory: bool) -> dict:
    endpoint = "/chat/compare" if compare_mode else "/chat"
    payload = {
        "message": message,
        "session_id": st.session_state.session_id,
        "use_memory": use_memory,
    }
    response = requests.post(
        f"{BACKEND_URL}{endpoint}",
        json=payload,
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


def evaluation_metrics(messages):
    assistant_messages = [msg for msg in messages if msg["role"] == "assistant"]
    if not assistant_messages:
        return {
            "responses": 0,
            "avg_latency_ms": 0,
            "avg_sources": 0,
            "rated_accuracy": "Not rated",
            "grounded_rate": "0%",
        }

    latencies = [msg["latency_ms"] for msg in assistant_messages]
    source_counts = [msg["source_count"] for msg in assistant_messages]
    grounded_count = sum(1 for msg in assistant_messages if msg["source_count"] >= 1)
    feedback_map = {"accurate": 1.0, "partially accurate": 0.5, "inaccurate": 0.0}
    feedback_scores = [
        feedback_map[msg["feedback"]]
        for msg in assistant_messages
        if msg.get("feedback") in feedback_map
    ]
    rated_accuracy = f"{round(mean(feedback_scores) * 100)}%" if feedback_scores else "Not rated"

    return {
        "responses": len(assistant_messages),
        "avg_latency_ms": round(mean(latencies)),
        "avg_sources": round(mean(source_counts), 1),
        "rated_accuracy": rated_accuracy,
        "grounded_rate": f"{round(grounded_count / len(assistant_messages) * 100)}%",
    }


def render_feedback_controls(message_index: int):
    message = st.session_state.messages[message_index]
    if message["role"] != "assistant":
        return
    if message.get("feedback"):
        st.caption(f"Evaluation: {message['feedback'].title()}")
        return

    with st.expander("Rate answer (optional)", expanded=False):
        col1, col2, col3 = st.columns(3)
        if col1.button("Accurate", key=f"fb-accurate-{message_index}", use_container_width=True):
            st.session_state.messages[message_index]["feedback"] = "accurate"
            st.rerun()
        if col2.button("Partial", key=f"fb-partial-{message_index}", use_container_width=True):
            st.session_state.messages[message_index]["feedback"] = "partially accurate"
            st.rerun()
        if col3.button("Inaccurate", key=f"fb-inaccurate-{message_index}", use_container_width=True):
            st.session_state.messages[message_index]["feedback"] = "inaccurate"
            st.rerun()


def render_single_response(message):
    st.markdown("#### Answer")
    st.markdown(message["answer"])
    st.markdown("#### Sources")
    st.markdown(
        " ".join(f'<span class="source-pill">{source}</span>' for source in message["sources"]),
        unsafe_allow_html=True,
    )
    st.markdown("#### Confidence")
    st.markdown(f"{message['confidence']} (retrieved from {len(message['sources'])} source references)")
    st.caption(f"Latency: {message['latency_ms'] / 1000:.2f}s")


def render_compare_response(message):
    st.markdown("#### OpenAI Response")
    st.markdown(message["openai"]["response"])
    st.markdown(
        " ".join(f'<span class="source-pill">{source}</span>' for source in message["openai"]["sources"]),
        unsafe_allow_html=True,
    )
    st.caption(f"Confidence: {message['openai']['confidence']}")
    st.markdown("---")
    st.markdown("#### Fine-Tuned Model Response")
    st.markdown(message["hf"]["response"])
    st.markdown(
        " ".join(f'<span class="source-pill">{source}</span>' for source in message["hf"]["sources"]),
        unsafe_allow_html=True,
    )
    st.caption(f"Confidence: {message['hf']['confidence']}")
    st.caption(f"Latency: {message['latency_ms'] / 1000:.2f}s")


st.set_page_config(
    page_title="Global Banking & Finance AI Assistant V2",
    page_icon="\U0001F3E6",
    layout="wide",
)

st.markdown(
    """
    <style>
    .block-container {
        max-width: 1260px;
        padding-top: 1.6rem;
        padding-bottom: 2rem;
    }
    .stApp {
        background:
            radial-gradient(circle at top right, rgba(12, 74, 110, 0.12), transparent 28%),
            radial-gradient(circle at top left, rgba(30, 64, 175, 0.10), transparent 24%),
            linear-gradient(180deg, #f8fbff 0%, #eef4f8 100%);
    }
    .hero-card, .info-card {
        background: rgba(255, 255, 255, 0.92);
        border: 1px solid rgba(15, 23, 42, 0.08);
        border-radius: 18px;
        padding: 1.1rem 1rem;
        box-shadow: 0 10px 30px rgba(15, 23, 42, 0.07);
        backdrop-filter: blur(6px);
    }
    .hero-kicker {
        color: #0f766e;
        font-size: 0.82rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 0.35rem;
    }
    .hero-title {
        color: #0f172a;
        font-size: 2rem;
        font-weight: 800;
        line-height: 1.15;
        margin-bottom: 0.5rem;
    }
    .hero-copy {
        color: #334155;
        line-height: 1.65;
        margin-bottom: 0.85rem;
    }
    .badge-row {
        display: flex;
        flex-wrap: wrap;
        gap: 0.45rem;
    }
    .badge {
        display: inline-block;
        padding: 0.35rem 0.65rem;
        border-radius: 999px;
        background: #eef2ff;
        color: #1e3a8a;
        font-size: 0.84rem;
        font-weight: 600;
    }
    .section-label {
        color: #1d4ed8;
        font-size: 0.8rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 0.45rem;
    }
    .chat-shell {
        background: rgba(255, 255, 255, 0.72);
        border: 1px solid rgba(15, 23, 42, 0.06);
        border-radius: 22px;
        padding: 0.4rem 0.55rem 0.85rem;
        box-shadow: 0 14px 36px rgba(15, 23, 42, 0.06);
    }
    .assistant-card {
        background: #ffffff;
        border: 1px solid rgba(12, 74, 110, 0.08);
        border-radius: 18px;
        padding: 1rem;
        margin-top: 0.4rem;
    }
    .source-pill {
        display: inline-block;
        margin: 0.1rem 0.35rem 0.35rem 0;
        padding: 0.28rem 0.58rem;
        border-radius: 999px;
        background: #ecfeff;
        color: #155e75;
        font-size: 0.82rem;
        font-weight: 600;
    }
    .footer-note {
        color: #64748b;
        font-size: 0.9rem;
        text-align: center;
        margin-top: 1.6rem;
    }
    .stChatMessage {
        border-radius: 16px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

ensure_session_state()

if not BACKEND_URL:
    st.error("BANKING_V2_API_URL is not set. Add it in Hugging Face Space Settings -> Variables or Secrets.")
    st.stop()

with st.sidebar:
    st.markdown("## Try These Questions")
    st.markdown("- What are the main KYC requirements for banks?")
    st.markdown("- Compare AML obligations in India and the U.S.")
    st.markdown("- Summarize RBI guidance on due diligence.")
    st.markdown("- Explain CECL in simple terms.")
    compare_mode = st.toggle("Enable compare mode", value=False, help="Compare OpenAI and the fine-tuned model on the same retrieved context.")
    use_memory = st.toggle("Use conversational memory", value=True, help="Keep multi-turn session history in the Version B backend.")
    st.caption(f"Session ID: `{st.session_state.session_id}`")

    st.markdown("---")
    st.markdown("## What This App Demonstrates")
    st.markdown("- FastAPI orchestration over the banking RAG flow")
    st.markdown("- Shared retrieval before generation")
    st.markdown("- Compare mode across model backends")
    st.markdown("- Session-aware memory for follow-up questions")
    st.markdown("- Same product feel as Version A with an upgraded backend")

    st.button("Clear Chat", use_container_width=True, on_click=clear_conversation)

st.title("\U0001F3E6 Global Banking & Finance AI Assistant V2")
st.caption(
    "Version B of the banking GenAI system with FastAPI orchestration, shared retrieval, conversational memory, "
    "and side-by-side backend comparison."
)
st.markdown("**Built by Rakesh Madasani**")
st.markdown("Frontend in Streamlit | Backend in FastAPI | Retrieval shared once before generation")
st.markdown(
    "Designed as an upgraded engineering version of the baseline assistant while preserving the original app."
)
st.info(
    "For educational and portfolio use only. Responses are grounded on retrieved banking content and are not legal, "
    "compliance, investment, or financial advice."
)
st.caption("Version B focuses on orchestration depth, compare mode, and conversational memory without changing Version A.")

hero_col, info_col = st.columns([1.65, 1.05], gap="large")
with hero_col:
    st.markdown(
        """
        <div class="hero-card">
            <div class="hero-kicker">Integrated GenAI System</div>
            <div class="hero-title">Shared retrieval, conversational memory, and backend comparison for banking AI</div>
            <div class="hero-copy">
                The same grounded banking context can power a standard answer flow or a side-by-side comparison
                between a general-purpose model and a domain-adapted model. This keeps the interface familiar
                while making the backend architecture more inspectable.
            </div>
            <div class="badge-row">
                <span class="badge">FastAPI orchestration</span>
                <span class="badge">Shared retrieval once</span>
                <span class="badge">Memory-aware chat</span>
                <span class="badge">Compare mode</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with info_col:
    st.markdown(
        """
        <div class="info-card">
            <div class="section-label">What This Demonstrates</div>
            <div style="color:#334155; line-height:1.7;">
                Backend orchestration separate from the frontend<br>
                Shared retrieval before generation<br>
                Multi-turn memory and summarization support<br>
                Side-by-side answer comparison on identical context<br>
                Evaluation-ready architecture for Version A vs Version B
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

metrics = evaluation_metrics(st.session_state.messages)
metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
metric_col1.metric("Backend URL", "Configured" if BACKEND_URL else "Missing")
metric_col2.metric("Compare Mode", "On" if compare_mode else "Off")
metric_col3.metric("Avg Latency", f"{metrics['avg_latency_ms']} ms")
metric_col4.metric("User-Rated Accuracy", metrics["rated_accuracy"])

dash_col1, dash_col2, dash_col3 = st.columns(3)
dash_col1.metric("Session Responses", metrics["responses"])
dash_col2.metric("Avg Sources / Answer", metrics["avg_sources"])
dash_col3.metric("Grounded Response Rate", metrics["grounded_rate"])

with st.expander("System Architecture", expanded=False):
    st.markdown(
        """
1. The Streamlit frontend sends each message to the Version B FastAPI backend.
2. The backend applies session memory and summarization when needed.
3. Retrieval runs once over the shared banking knowledge base.
4. The same retrieved context is used for a single answer or fanned out to both backends in compare mode.
5. The frontend renders sources, confidence, and response comparison without changing the Version A visual language.

**Stack:** Streamlit, FastAPI, FAISS, Python, OpenAI, local HF model path
"""
    )

examples = [
    "How does FDIC insurance work and what deposits are covered?",
    "Compare CTR reporting thresholds in the U.S. and India?",
    "Explain Regulation E liability limits for unauthorized transfers?",
    "Explain Basel III capital adequacy requirements in simple terms.",
    "What documents are required for KYC of an individual in India?",
    "How does Basel III differ from Basel II?",
]

st.markdown("**Try a question:**")
example_columns = st.columns(2)
selected = None
for index, example in enumerate(examples):
    if example_columns[index % 2].button(example, use_container_width=True):
        selected = example

st.markdown('<div class="chat-shell">', unsafe_allow_html=True)
for idx, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        if message["role"] == "user":
            st.markdown(message["content"])
        else:
            st.markdown('<div class="assistant-card">', unsafe_allow_html=True)
            if message.get("compare_mode"):
                render_compare_response(message)
            else:
                render_single_response(message)
            render_feedback_controls(idx)
            st.caption("AI can make mistakes. Verify important banking, compliance, or legal details with official sources.")
            st.markdown("</div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

question = st.chat_input(
    "Ask about KYC, AML, RBI guidelines, U.S. banking rules, credit risk, or compare regulations..."
) or selected

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Calling Version B backend and assembling grounded response..."):
            started = time.perf_counter()
            try:
                result = call_backend(question, compare_mode=compare_mode, use_memory=use_memory)
                latency_ms = round((time.perf_counter() - started) * 1000)
                st.markdown('<div class="assistant-card">', unsafe_allow_html=True)
                if compare_mode:
                    openai_result = result["openai_response"]
                    hf_result = result["hf_model_response"]
                    render_compare_response(
                        {
                            "openai": openai_result,
                            "hf": hf_result,
                            "latency_ms": latency_ms,
                        }
                    )
                    source_count = max(len(openai_result["sources"]), len(hf_result["sources"]))
                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "compare_mode": True,
                            "openai": openai_result,
                            "hf": hf_result,
                            "latency_ms": latency_ms,
                            "source_count": source_count,
                            "feedback": None,
                        }
                    )
                else:
                    render_single_response(
                        {
                            "answer": result["response"],
                            "sources": result["sources"],
                            "confidence": result["confidence"],
                            "latency_ms": latency_ms,
                        }
                    )
                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "compare_mode": False,
                            "answer": result["response"],
                            "sources": result["sources"],
                            "confidence": result["confidence"],
                            "latency_ms": latency_ms,
                            "source_count": len(result["sources"]),
                            "feedback": None,
                        }
                    )
                st.caption("AI can make mistakes. Verify important banking, compliance, or legal details with official sources.")
                st.markdown("</div>", unsafe_allow_html=True)
            except requests.HTTPError as exc:
                st.error(f"Backend returned an error: {exc.response.text}")
            except Exception as exc:
                st.error(f"Error while calling the Version B backend: {exc}")

st.markdown(
    '<div class="footer-note">Built by Rakesh Madasani | Version B Streamlit client over FastAPI banking backend | 2026</div>',
    unsafe_allow_html=True,
)
