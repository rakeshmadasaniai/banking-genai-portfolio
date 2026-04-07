import re

from langchain_core.prompts import PromptTemplate

from app.config import (
    FALLBACK_ANSWER,
    LLM_BACKEND,
    LOCAL_HF_ADAPTER_ID,
    LOCAL_HF_DEVICE,
    LOCAL_HF_MODEL_ID,
    OPENAI_API_KEY,
    OPENAI_MODEL,
)


try:
    from langchain_openai import ChatOpenAI
except Exception:  # pragma: no cover
    ChatOpenAI = None


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

_client_cache: dict[str, object] = {}


class OpenAIBackend:
    def __init__(self):
        if ChatOpenAI is None:
            raise RuntimeError("langchain-openai is not installed for the OpenAI backend.")
        if not OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY is not set.")
        self.client = ChatOpenAI(model=OPENAI_MODEL, api_key=OPENAI_API_KEY, temperature=0.1, max_tokens=220)

    def invoke(self, prompt: str) -> str:
        return self.client.invoke(prompt).content.strip()


class LocalHFBackend:
    def __init__(self):
        try:
            import torch
            from peft import PeftModel
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except Exception as exc:  # pragma: no cover
            raise RuntimeError(
                "Local HF backend requires transformers, peft, and torch in a compatible environment."
            ) from exc

        self.torch = torch
        self.tokenizer = AutoTokenizer.from_pretrained(LOCAL_HF_MODEL_ID)
        base_model = AutoModelForCausalLM.from_pretrained(
            LOCAL_HF_MODEL_ID,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map=LOCAL_HF_DEVICE,
        )
        self.model = PeftModel.from_pretrained(base_model, LOCAL_HF_ADAPTER_ID)
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


def get_backend(name: str | None = None):
    backend_name = (name or LLM_BACKEND).strip().lower()
    if backend_name not in _client_cache:
        if backend_name == "openai":
            _client_cache[backend_name] = OpenAIBackend()
        elif backend_name == "local_hf":
            _client_cache[backend_name] = LocalHFBackend()
        else:
            raise RuntimeError(f"Unsupported backend '{backend_name}'. Use 'openai' or 'local_hf'.")
    return _client_cache[backend_name]


def format_history(history: list[dict[str, str]]) -> str:
    if not history:
        return "No earlier conversation."
    return "\n".join(f"{turn.get('role', 'unknown').title()}: {turn.get('content', '').strip()}" for turn in history)


def is_simple_factual_query(query: str) -> bool:
    comparison_terms = ("compare", "difference", "differences", "versus", "vs", "india", "u.s.", "us")
    lowered_query = query.lower()
    return len(query.split()) <= 10 and not any(term in lowered_query for term in comparison_terms)


def is_comparison_query(query: str) -> bool:
    comparison_terms = ("compare", "difference", "differences", "versus", "vs", "india", "u.s.", "us")
    lowered_query = query.lower()
    return any(term in lowered_query for term in comparison_terms)


def extractive_answer(context_docs, question: str) -> str:
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
