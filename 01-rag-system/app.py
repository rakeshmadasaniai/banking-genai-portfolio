import hashlib
import os
import re
import time
from io import BytesIO
from pathlib import Path
from statistics import mean

import streamlit as st
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader


OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
DOCS_DIR = Path(".")
DOC_GLOB = "*knowledge*.txt"
COMPARISON_TERMS = ("compare", "difference", "differences", "versus", "vs", "india", "u.s.", "us")
FALLBACK_ANSWER = "I don't have sufficient information on that topic in my knowledge base."

RAG_PROMPT = PromptTemplate(
    input_variables=["context", "question"],
    template="""Answer only from the provided context.

If the answer is not supported by the context, say:
"I don't have sufficient information on that topic in my knowledge base."

Be concise and professional.

Context:
{context}

Question: {question}

Answer:""",
)

COMPARISON_RAG_PROMPT = PromptTemplate(
    input_variables=["context", "question"],
    template="""Answer only from the provided context.

If the answer is not supported by the context, say:
"I don't have sufficient information on that topic in my knowledge base."

If the question asks for a comparison, combine facts across the provided source excerpts when each part of the comparison is supported.
Be concise, explicit, and mention the key difference directly.

Context:
{context}

Question: {question}

Answer:""",
)


def load_text_documents():
    documents = []
    for path in sorted(DOCS_DIR.glob(DOC_GLOB)):
        text = path.read_text(encoding="utf-8")
        documents.append(Document(page_content=text, metadata={"source": path.name, "type": "base"}))
    return documents


def split_documents(documents):
    splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=80)
    return splitter.split_documents(documents)


@st.cache_resource
def get_embeddings():
    return HuggingFaceEmbeddings(model_name=EMBED_MODEL)


@st.cache_resource
def get_base_index():
    base_docs = load_text_documents()
    base_chunks = split_documents(base_docs)
    vectorstore = FAISS.from_documents(base_chunks, get_embeddings())
    retriever = vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs={"k": 3, "fetch_k": 10, "lambda_mult": 0.7},
    )
    return retriever, len(base_docs), len(base_chunks)


@st.cache_resource
def get_llm():
    return ChatOpenAI(model=OPENAI_MODEL, api_key=OPENAI_API_KEY, temperature=0.1, max_tokens=220)


def uploaded_signature(uploaded_files):
    if not uploaded_files:
        return ""
    parts = []
    for uploaded in uploaded_files:
        payload = uploaded.getvalue()
        parts.append(f"{uploaded.name}:{len(payload)}:{hashlib.md5(payload).hexdigest()}")
    return "|".join(parts)


def parse_uploaded_pdfs(uploaded_files):
    documents = []
    for uploaded in uploaded_files:
        try:
            reader = PdfReader(BytesIO(uploaded.getvalue()))
            for page_number, page in enumerate(reader.pages, start=1):
                text = (page.extract_text() or "").strip()
                if not text:
                    continue
                documents.append(
                    Document(
                        page_content=text,
                        metadata={
                            "source": uploaded.name,
                            "page": page_number,
                            "type": "uploaded",
                        },
                    )
                )
        except Exception:
            st.warning(f"Skipped {uploaded.name} because it could not be parsed as a readable PDF.")
    return documents


def build_uploaded_retriever(uploaded_files):
    documents = parse_uploaded_pdfs(uploaded_files)
    if not documents:
        return None, 0, 0
    chunks = split_documents(documents)
    vectorstore = FAISS.from_documents(chunks, get_embeddings())
    retriever = vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs={"k": 3, "fetch_k": 8, "lambda_mult": 0.7},
    )
    return retriever, len(documents), len(chunks)


def retrieve_context(query, base_retriever, uploaded_retriever=None):
    lowered_query = query.lower()
    per_retriever_limit = 2 if len(query.split()) <= 10 and not any(term in lowered_query for term in COMPARISON_TERMS) else 3

    combined = []
    seen = set()
    retriever_plan = []
    if uploaded_retriever:
        retriever_plan.append((uploaded_retriever, per_retriever_limit))
    retriever_plan.append((base_retriever, per_retriever_limit))

    for retriever, limit in retriever_plan:
        if not retriever:
            continue
        added = 0
        for doc in retriever.invoke(query):
            key = (
                doc.metadata.get("source", "unknown"),
                doc.metadata.get("page", ""),
                doc.page_content[:160],
            )
            if key in seen:
                continue
            seen.add(key)
            combined.append(doc)
            added += 1
            if added >= limit:
                break
    final_limit = 2 if per_retriever_limit == 2 else 4
    return combined[:final_limit]


def source_label(doc):
    source = doc.metadata.get("source", "unknown")
    page = doc.metadata.get("page")
    return f"{source} (page {page})" if page else source


def build_context(context_docs, char_limit):
    sections = []
    for doc in context_docs:
        label = source_label(doc)
        snippet = doc.page_content[:char_limit].strip()
        sections.append(f"[Source: {label}]\n{snippet}")
    return "\n\n".join(sections)


def boosted_context(question, context_docs, base_context):
    lowered_question = question.lower()
    if not is_comparison_query(question):
        return base_context

    priority_terms = []
    for term in ("ctr", "sar", "fdic", "regulation e", "basel", "kyc", "aml"):
        if term in lowered_question:
            priority_terms.append(term)

    if not priority_terms:
        return base_context

    highlighted = []
    for doc in context_docs:
        sentences = re.split(r"(?<=[.!?])\s+", doc.page_content.strip())
        for sentence in sentences:
            normalized_sentence = sentence.lower()
            if any(term in normalized_sentence for term in priority_terms):
                highlighted.append(f"[Priority source: {source_label(doc)}]\n{sentence.strip()}")
                if len(highlighted) >= 4:
                    break
        if len(highlighted) >= 4:
            break

    if not highlighted:
        return base_context
    return "\n\n".join(highlighted) + "\n\n" + base_context


def is_simple_factual_query(query):
    lowered_query = query.lower()
    return len(query.split()) <= 10 and not any(term in lowered_query for term in COMPARISON_TERMS)


def is_comparison_query(query):
    lowered_query = query.lower()
    return any(term in lowered_query for term in COMPARISON_TERMS)


def extractive_answer(context_docs, question):
    if not context_docs:
        return ""

    keywords = {
        token.lower()
        for token in re.findall(r"[A-Za-z0-9]+", question)
        if len(token) > 3 and token.lower() not in {"what", "does", "work", "works", "covered", "cover", "with", "from", "that", "this"}
    }
    sentences = re.split(r"(?<=[.!?])\s+", context_docs[0].page_content.strip())
    scored = []
    for sentence in sentences:
        sentence_tokens = set(re.findall(r"[A-Za-z0-9]+", sentence.lower()))
        overlap = len(keywords & sentence_tokens)
        if sentence.strip():
            scored.append((overlap, sentence.strip()))

    if not scored:
        return ""

    scored.sort(key=lambda item: item[0], reverse=True)
    best_sentences = [sentence for overlap, sentence in scored if overlap > 0][:2]
    if not best_sentences:
        best_sentences = [sentence for _, sentence in scored[:2]]
    return " ".join(best_sentences).strip()


def confidence_label(source_count, answer_text="", extractive=False):
    normalized_answer = answer_text.strip()
    if normalized_answer == FALLBACK_ANSWER or source_count == 0:
        return "Low"
    if extractive and source_count >= 1:
        return "High"
    if source_count >= 3:
        return "High"
    if source_count == 2:
        return "Moderate"
    if source_count == 1:
        return "Moderate"
    return "Low"


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
    source_counts = [len(msg["sources"]) for msg in assistant_messages]
    grounded_count = sum(
        1
        for msg in assistant_messages
        if msg["answer"].strip() != FALLBACK_ANSWER
        and len(msg["sources"]) >= 1
        and any(preview["content"].strip() for preview in msg.get("previews", []))
    )
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


def clear_conversation():
    st.session_state.messages = []


def render_feedback_controls(message_index):
    message = st.session_state.messages[message_index]
    if message["role"] != "assistant":
        return
    if message.get("feedback"):
        st.caption(f"Evaluation: {message['feedback'].title()}")
        return

    with st.expander("Rate answer (optional)", expanded=False):
        st.caption("Use this only when you want to evaluate the response quality.")
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


st.set_page_config(
    page_title="Global Banking & Finance AI Assistant",
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

if "messages" not in st.session_state:
    st.session_state.messages = []
if "upload_signature" not in st.session_state:
    st.session_state.upload_signature = ""
if "uploaded_retriever" not in st.session_state:
    st.session_state.uploaded_retriever = None
if "uploaded_doc_count" not in st.session_state:
    st.session_state.uploaded_doc_count = 0
if "uploaded_chunk_count" not in st.session_state:
    st.session_state.uploaded_chunk_count = 0

if not OPENAI_API_KEY:
    st.error("OPENAI_API_KEY is not set. Add it in Hugging Face Space Settings -> Secrets.")
    st.stop()

base_retriever, base_doc_count, base_chunk_count = get_base_index()
llm = get_llm()

with st.sidebar:
    st.markdown("## Try These Questions")
    st.markdown("- What are the main KYC requirements for banks?")
    st.markdown("- Compare AML obligations in India and the U.S.")
    st.markdown("- Summarize RBI guidance on due diligence.")
    st.markdown("- Explain CECL in simple terms.")

    uploaded_files = st.file_uploader(
        "Upload PDF documents for dynamic RAG",
        type="pdf",
        accept_multiple_files=True,
        help="Uploaded PDFs are indexed for this session and used alongside the banking knowledge base.",
    )

    current_signature = uploaded_signature(uploaded_files)
    if current_signature != st.session_state.upload_signature:
        if uploaded_files:
            with st.spinner("Indexing uploaded PDFs..."):
                retriever, upload_docs, upload_chunks = build_uploaded_retriever(uploaded_files)
            st.session_state.uploaded_retriever = retriever
            st.session_state.uploaded_doc_count = upload_docs
            st.session_state.uploaded_chunk_count = upload_chunks
        else:
            st.session_state.uploaded_retriever = None
            st.session_state.uploaded_doc_count = 0
            st.session_state.uploaded_chunk_count = 0
        st.session_state.upload_signature = current_signature

    st.markdown("---")
    st.markdown("## What This App Demonstrates")
    st.markdown("- RAG for regulated domains")
    st.markdown("- Semantic retrieval with FAISS")
    st.markdown("- OpenAI-powered response generation")
    st.markdown("- Prompt engineering for grounded Q&A")
    st.markdown("- Hybrid retrieval across built-in knowledge and uploaded PDFs")

    st.button("Clear Chat", use_container_width=True, on_click=clear_conversation)

st.title("\U0001F3E6 Global Banking & Finance AI Assistant(RAG)")
st.caption(
    "OpenAI-powered Retrieval-Augmented Generation(RAG) system for grounded banking and compliance Q&A across "
    "U.S. and India regulations."
)
st.markdown("**Built by Rakesh Madasani**")
st.markdown("Built using OpenAI, LangChain, FAISS, and Streamlit")
st.markdown(
    "Designed to simulate real-world AI systems used in banking, fintech, and compliance automation."
)
st.info(
    "For educational and portfolio use only. Responses are generated from "
    "retrieved regulatory content and are not legal, compliance, investment, "
    "or financial advice."
)
st.caption("Optimized for low-latency, high quality responses using efficient retrieval and prompt engineering")

hero_col, info_col = st.columns([1.65, 1.05], gap="large")
with hero_col:
    st.markdown(
        """
        <div class="hero-card">
            <div class="hero-kicker">Production-Ready RAG System</div>
            <div class="hero-title">Grounded finance answers across U.S. and India banking regulations</div>
            <div class="hero-copy">
                A polished AI system for regulatory question answering with source-grounded retrieval,
                dynamic PDF ingestion, evaluation signals, and a deployable product-style interface.
            </div>
            <div class="badge-row">
                <span class="badge">OpenAI-powered generation</span>
                <span class="badge">FAISS retrieval</span>
                <span class="badge">LangChain pipeline</span>
                <span class="badge">Compliance-focused prompting</span>
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
                Retrieval grounding and source transparency<br>
                Prompt design for regulated-domain Q&amp;A<br>
                Hybrid retrieval across base docs and uploaded PDFs<br>
                Dynamic PDF upload + live indexing<br>
                Evaluation framework with 100+ test queries
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

metrics = evaluation_metrics(st.session_state.messages)
metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
metric_col1.metric("Base Knowledge Files", base_doc_count)
metric_col2.metric("Uploaded PDF Pages", st.session_state.uploaded_doc_count)
metric_col3.metric("Avg Latency", f"{metrics['avg_latency_ms']} ms")
metric_col4.metric("User-Rated Accuracy", metrics["rated_accuracy"])

dash_col1, dash_col2, dash_col3 = st.columns(3)
dash_col1.metric("Session Responses", metrics["responses"])
dash_col2.metric("Avg Sources / Answer", metrics["avg_sources"])
dash_col3.metric("Grounded Response Rate", metrics["grounded_rate"])

with st.expander("System Architecture", expanded=False):
    st.markdown(
        f"""
1. Source documents are loaded from the embedded banking knowledge base and optional uploaded PDFs.
2. Documents are chunked and embedded using `sentence-transformers/all-MiniLM-L6-v2`.
3. FAISS retrieves the most relevant chunks for each question.
4. OpenAI generates the final grounded response from the retrieved context.
5. Session feedback records helpfulness and quality signals for quick evaluation.

**Stack:** OpenAI API, LangChain, FAISS, Streamlit, Python  
**Indexed Chunks:** {base_chunk_count + st.session_state.uploaded_chunk_count}
"""
    )

examples = [
    "How does FDIC insurance work and what deposits are covered?",
    "Compare CTR reporting thresholds in the U.S. and India?",
    "Explain Regulation E liability limits for unauthorized transfers?",
    "Explain Basel III capital adequacy requirements in simple terms.",
    "What documents are required for KYC of an individual in India?",
    "Based on the uploaded PDF, what additional compliance guidance applies to high-risk customers?",
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
            st.markdown("#### Answer")
            st.markdown(message["answer"])
            st.markdown("#### Sources")
            st.markdown(
                " ".join(
                    f'<span class="source-pill">{source}</span>' for source in message["sources"]
                ),
                unsafe_allow_html=True,
            )
            st.markdown("#### Confidence")
            st.markdown(
                f"{message['confidence']} (retrieved from {len(message['sources'])} source references)"
            )
            latency_seconds = message["latency_ms"] / 1000
            st.caption(f"Latency: {latency_seconds:.2f}s")
            with st.expander("Retrieved Sources & Context"):
                for preview_index, preview in enumerate(message["previews"], start=1):
                    st.markdown(f"**Doc {preview_index} - {preview['label']}**")
                    st.write(preview["content"])
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
        with st.spinner("Analyzing documents and generating grounded response..."):
            start = time.perf_counter()
            try:
                context_docs = retrieve_context(
                    question,
                    base_retriever=base_retriever,
                    uploaded_retriever=st.session_state.uploaded_retriever,
                )
                context_char_limit = 550 if is_comparison_query(question) else 350
                context = build_context(context_docs, context_char_limit)
                context = boosted_context(question, context_docs, context)
                source_names = [source_label(doc) for doc in context_docs]
                unique_sources = list(dict.fromkeys(source_names))
                previews = []
                for doc in context_docs:
                    preview = doc.page_content[:400]
                    if len(doc.page_content) > 400:
                        preview += "..."
                    previews.append({"label": source_label(doc), "content": preview})

                st.markdown('<div class="assistant-card">', unsafe_allow_html=True)
                st.markdown("#### Answer")
                used_extractive_path = False
                if is_simple_factual_query(question) and unique_sources:
                    answer = extractive_answer(context_docs, question) or FALLBACK_ANSWER
                    used_extractive_path = answer != FALLBACK_ANSWER
                    st.markdown(answer)
                else:
                    prompt_template = COMPARISON_RAG_PROMPT if is_comparison_query(question) else RAG_PROMPT
                    prompt_text = prompt_template.format(context=context, question=question)

                    def stream_answer():
                        for chunk in llm.stream(prompt_text):
                            if chunk.content:
                                yield chunk.content

                    answer = st.write_stream(stream_answer).strip()

                confidence = confidence_label(
                    len(unique_sources),
                    answer_text=answer,
                    extractive=used_extractive_path,
                )
                latency_ms = round((time.perf_counter() - start) * 1000)
                st.markdown("#### Sources")
                st.markdown(
                    " ".join(f'<span class="source-pill">{name}</span>' for name in unique_sources),
                    unsafe_allow_html=True,
                )
                st.markdown("#### Confidence")
                st.markdown(f"{confidence} (retrieved from {len(unique_sources)} source references)")
                st.caption(f"Latency: {latency_ms / 1000:.2f}s")
                with st.expander("Retrieved Sources & Context"):
                    for preview_index, preview in enumerate(previews, start=1):
                        st.markdown(f"**Doc {preview_index} - {preview['label']}**")
                        st.write(preview["content"])
                st.caption("AI can make mistakes. Verify important banking, compliance, or legal details with official sources.")
                st.markdown("</div>", unsafe_allow_html=True)

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": answer,
                        "answer": answer,
                        "sources": unique_sources,
                        "confidence": confidence,
                        "latency_ms": latency_ms,
                        "previews": previews,
                        "feedback": None,
                    }
                )
            except Exception as exc:
                st.error(f"Error while generating a response: {exc}")

st.markdown(
    '<div class="footer-note">Built by Rakesh Madasani | OpenAI-powered RAG system | 2026</div>',
    unsafe_allow_html=True,
)

