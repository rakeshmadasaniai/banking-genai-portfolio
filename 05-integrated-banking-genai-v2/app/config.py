from pathlib import Path
import os


BASE_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BASE_DIR.parents[0]
VERSION_A_DIR = PROJECT_ROOT / "01-rag-system"

APP_TITLE = "Banking GenAI System V2"
APP_VERSION = "1.0.0"

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
LLM_BACKEND = os.environ.get("LLM_BACKEND", "openai").strip().lower()
LOCAL_HF_MODEL_ID = os.environ.get("LOCAL_HF_MODEL_ID", "mistralai/Mistral-7B-Instruct-v0.3")
LOCAL_HF_ADAPTER_ID = os.environ.get("LOCAL_HF_ADAPTER_ID", "RakeshMadasani/banking-finance-mistral-qlora")
LOCAL_HF_DEVICE = os.environ.get("LOCAL_HF_DEVICE", "auto")

EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
DOC_GLOB = "*knowledge*.txt"
MAX_TURNS = 10
RECENT_TURNS = 4
VECTOR_SEARCH_K = 3
VECTOR_SEARCH_FETCH_K = 10
VECTOR_LAMBDA = 0.7

COMPARISON_TERMS = ("compare", "difference", "differences", "versus", "vs", "india", "u.s.", "us")
FALLBACK_ANSWER = "I don't have sufficient information on that topic in my knowledge base."
