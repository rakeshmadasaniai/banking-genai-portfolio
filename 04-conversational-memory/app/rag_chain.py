import os
import re
from pathlib import Path
from typing import Any

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from langchain_text_splitters import RecursiveCharacterTextSplitter


try:
    from langchain_openai import ChatOpenAI
except Exception:  # pragma: no cover - optional dependency at runtime
    ChatOpenAI = None


OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
LLM_BACKEND = os.environ.get("LLM_BACKEND", "openai").strip().lower()
LOCAL_HF_MODEL_ID = os.environ.get("LOCAL_HF_MODEL_ID", "mistralai/Mistral-7B-Instruct-v0.3")
LOCAL_HF_ADAPTER_ID = os.environ.get("LOCAL_HF_ADAPTER_ID", "RakeshMadasani/banking-finance-mistral-qlora")
LOCAL_HF_DEVICE = os.environ.get("LOCAL_HF_DEVICE", "auto")
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
COMPARISON_TERMS = ("compare", "difference", "differences", "versus", "vs", "india", "u.s.", "us")
FALLBACK_ANSWER = "I don't have sufficient information on that topic in my knowledge base."
KNOWLEDGE_DIR = Path(__file__).resolve().parents[2] / "01-rag-system"
DOC_GLOB = "*knowledge*.txt"

RAG_PROMPT = PromptTemplate(
    input_variables=["history", "context", "question"],
    template="""You are a banking and compliance assistant.

Use the retrieved context and conversation history when available.
Answer only from the provided context.

If the answer is not supported by the context, say:
"I don't have sufficient information on that topic in my knowledge base."

Be concise and professional.

Conversation history:
{history}

Context:
{context}

Question: {question}

Answer:""",
)

COMPARISON_RAG_PROMPT = PromptTemplate(
    input_variables=["history", "context", "question"],
    template="""You are a banking and compliance assistant.

Use the retrieved context and conversation history when available.
Answer only from the provided context.

If the answer is not supported by the context, say:
"I don't have sufficient information on that topic in my knowledge base."

If the question asks for a comparison, combine facts across the provided source excerpts when each part of the comparison is supported.
Be concise, explicit, and mention the key difference directly.

Conversation history:
{history}

Context:
{context}

Question: {question}

Answer:""",
)

_retriever = None
_backend_client = None
_backend_name = None


class OpenAIBackend:
    def __init__(self):
        if ChatOpenAI is None:
            raise RuntimeError("langchain-openai is not installed for the OpenAI backend.")
        if not OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY is not set for the conversational backend.")
        self.client = ChatOpenAI(
            model=OPENAI_MODEL,
            api_key=OPENAI_API_KEY,
            temperature=0.1,
            max_tokens=220,
        )

    def invoke(self, prompt: str) -> str:
        return self.client.invoke(prompt).content.strip()


class LocalHFBackend:
    def __init__(self):
        try:
            import torch
            from peft import PeftModel
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except Exception as exc:  # pragma: no cover - dependency import error
            raise RuntimeError(
                "Local HF backend requires transformers, peft, and torch. "
                "Install Project 4 requirements in a compatible environment."
            ) from exc

        self.torch = torch
        self.tokenizer = AutoTokenizer.from_pretrained(LOCAL_MODEL_ID)
        base_model = AutoModelForCausalLM.from_pretrained(
            LOCAL_MODEL_ID,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map=LOCAL_HF_DEVICE,
        )
        self.model = PeftModel.from_pretrained(base_model, LOCAL_ADAPTER_ID)
        self.model.eval()

    def invoke(self, prompt: str) -> str:
        inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=2048)
        model_device = getattr(self.model, "device", None)
        if model_device is not None:
            inputs = {key: value.to(model_device) for key, value in inputs.items()}

        with self.torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=220,
                do_sample=False,
                temperature=0.1,
                pad_token_id=self.tokenizer.eos_token_id,
            )

        generated = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        if generated.startswith(prompt):
            generated = generated[len(prompt):]
        return generated.strip()


def _load_text_documents() -> list[Document]:
    documents = []
    for path in sorted(KNOWLEDGE_DIR.glob(DOC_GLOB)):
        text = path.read_text(encoding="utf-8")
        documents.append(Document(page_content=text, metadata={"source": path.name, "type": "base"}))
    return documents


def _split_documents(documents: list[Document]) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=80)
    return splitter.split_documents(documents)


def _get_embeddings() -> HuggingFaceEmbeddings:
    return HuggingFaceEmbeddings(model_name=EMBED_MODEL)


def get_retriever():
    global _retriever
    if _retriever is None:
        base_docs = _load_text_documents()
        if not base_docs:
            raise RuntimeError("No banking knowledge files found for Project 4 retrieval.")
        base_chunks = _split_documents(base_docs)
        vectorstore = FAISS.from_documents(base_chunks, _get_embeddings())
        _retriever = vectorstore.as_retriever(
            search_type="mmr",
            search_kwargs={"k": 3, "fetch_k": 10, "lambda_mult": 0.7},
        )
    return _retriever


def get_llm(backend: str | None = None):
    global _backend_client, _backend_name
    selected_backend = (backend or LLM_BACKEND).strip().lower()
    if _backend_client is None or _backend_name != selected_backend:
        if selected_backend == "openai":
            _backend_client = OpenAIBackend()
        elif selected_backend == "local_hf":
            _backend_client = LocalHFBackend()
        else:
            raise RuntimeError(
                f"Unsupported LLM_BACKEND '{selected_backend}'. Use 'openai' or 'local_hf'."
            )
        _backend_name = selected_backend
    return _backend_client


def source_label(doc: Document) -> str:
    source = doc.metadata.get("source", "unknown")
    page = doc.metadata.get("page")
    return f"{source} (page {page})" if page else source


def is_simple_factual_query(query: str) -> bool:
    lowered_query = query.lower()
    return len(query.split()) <= 10 and not any(term in lowered_query for term in COMPARISON_TERMS)


def is_comparison_query(query: str) -> bool:
    lowered_query = query.lower()
    return any(term in lowered_query for term in COMPARISON_TERMS)


def retrieve_context(query: str, retriever) -> list[Document]:
    lowered_query = query.lower()
    limit = 2 if len(query.split()) <= 10 and not any(term in lowered_query for term in COMPARISON_TERMS) else 3

    combined = []
    seen = set()
    for doc in retriever.invoke(query):
        key = (doc.metadata.get("source", "unknown"), doc.page_content[:160])
        if key in seen:
            continue
        seen.add(key)
        combined.append(doc)
        if len(combined) >= limit:
            break
    final_limit = 2 if limit == 2 else 4
    return combined[:final_limit]


def build_context(context_docs: list[Document], char_limit: int) -> str:
    sections = []
    for doc in context_docs:
        label = source_label(doc)
        snippet = doc.page_content[:char_limit].strip()
        sections.append(f"[Source: {label}]\n{snippet}")
    return "\n\n".join(sections)


def boosted_context(question: str, context_docs: list[Document], base_context: str) -> str:
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

    return "\n\n".join(highlighted) + "\n\n" + base_context if highlighted else base_context


def extractive_answer(context_docs: list[Document], question: str) -> str:
    if not context_docs:
        return ""

    keywords = {
        token.lower()
        for token in re.findall(r"[A-Za-z0-9]+", question)
        if len(token) > 3 and token.lower() not in {"what", "does", "with", "from", "that", "this"}
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


def confidence_label(source_count: int, answer_text: str = "", extractive: bool = False) -> str:
    normalized_answer = answer_text.strip()
    if normalized_answer == FALLBACK_ANSWER or source_count == 0:
        return "Low"
    if extractive and source_count >= 1:
        return "High"
    if source_count >= 3:
        return "High"
    if source_count in (1, 2):
        return "Moderate"
    return "Low"


def format_history(history: list[dict[str, str]]) -> str:
    if not history:
        return "No earlier conversation."
    return "\n".join(f"{turn.get('role', 'unknown').title()}: {turn.get('content', '').strip()}" for turn in history)


def get_rag_response(
    question: str,
    history: list[dict[str, str]] | None = None,
    backend: str | None = None,
) -> dict[str, Any]:
    retriever = get_retriever()
    selected_backend = (backend or LLM_BACKEND).strip().lower()
    llm = get_llm(selected_backend)
    history = history or []

    context_docs = retrieve_context(question, retriever)
    context_char_limit = 550 if is_comparison_query(question) else 350
    context = build_context(context_docs, context_char_limit)
    context = boosted_context(question, context_docs, context)
    source_names = [source_label(doc) for doc in context_docs]
    unique_sources = list(dict.fromkeys(source_names))

    used_extractive_path = False
    if is_simple_factual_query(question) and unique_sources:
        answer = extractive_answer(context_docs, question) or FALLBACK_ANSWER
        used_extractive_path = answer != FALLBACK_ANSWER
    else:
        prompt_template = COMPARISON_RAG_PROMPT if is_comparison_query(question) else RAG_PROMPT
        prompt_text = prompt_template.format(
            history=format_history(history),
            context=context,
            question=question,
        )
        answer = llm.invoke(prompt_text)

    confidence = confidence_label(
        len(unique_sources),
        answer_text=answer,
        extractive=used_extractive_path,
    )

    return {
        "response": answer,
        "sources": unique_sources,
        "confidence": confidence,
        "history_used": bool(history),
        "backend": selected_backend,
    }
