import re
from functools import lru_cache

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import (
    COMPARISON_TERMS,
    DOC_GLOB,
    EMBED_MODEL,
    VECTOR_LAMBDA,
    VECTOR_SEARCH_FETCH_K,
    VECTOR_SEARCH_K,
    VERSION_A_DIR,
)


def load_text_documents() -> list[Document]:
    documents = []
    for path in sorted(VERSION_A_DIR.glob(DOC_GLOB)):
        text = path.read_text(encoding="utf-8")
        documents.append(Document(page_content=text, metadata={"source": path.name, "type": "base"}))
    return documents


def split_documents(documents: list[Document]) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=80)
    return splitter.split_documents(documents)


@lru_cache(maxsize=1)
def get_embeddings():
    return HuggingFaceEmbeddings(model_name=EMBED_MODEL)


@lru_cache(maxsize=1)
def get_retriever():
    base_docs = load_text_documents()
    if not base_docs:
        raise RuntimeError("No banking knowledge files found in Version A directory.")
    base_chunks = split_documents(base_docs)
    vectorstore = FAISS.from_documents(base_chunks, get_embeddings())
    return vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs={"k": VECTOR_SEARCH_K, "fetch_k": VECTOR_SEARCH_FETCH_K, "lambda_mult": VECTOR_LAMBDA},
    )


def source_label(doc: Document) -> str:
    source = doc.metadata.get("source", "unknown")
    page = doc.metadata.get("page")
    return f"{source} (page {page})" if page else source


def is_comparison_query(query: str) -> bool:
    lowered_query = query.lower()
    return any(term in lowered_query for term in COMPARISON_TERMS)


def retrieve_context_once(query: str) -> list[Document]:
    retriever = get_retriever()
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
