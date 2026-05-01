"""
INTEGRATION PATCH — product_runtime.py  (FIXED v2)
====================================================
Fixes applied vs v1:
  1. retriever=retriever now passed to run_agentic_workflow()
  2. Mode name unified to "Agentic Workspace" everywhere
  3. Consistent naming in MODEL_DESCRIPTIONS, sidebar radio, composer selectbox
  4. Verification method shown in trace (LLM judge vs heuristic)

Apply each patch by finding the FIND block and replacing with REPLACE block.
"""

# ══════════════════════════════════════════════════════════════════════════════
# PATCH 1 — Imports
# ══════════════════════════════════════════════════════════════════════════════

FIND_1 = """
from models.auto_router import run_auto_mode
from models.finetuned_mode import generate_finetuned_response
from models.openai_mode import generate_openai_response
"""

REPLACE_1 = """
from models.auto_router import run_auto_mode
from models.finetuned_mode import generate_finetuned_response
from models.openai_mode import generate_openai_response
from core.agentic_runtime import run_agentic_workflow
from features.agentic_ui import render_agent_trace, render_portfolio_table
"""


# ══════════════════════════════════════════════════════════════════════════════
# PATCH 2 — MODEL_DESCRIPTIONS (add Agentic Workspace)
# ══════════════════════════════════════════════════════════════════════════════

FIND_2 = """
MODEL_DESCRIPTIONS = {
    "OpenAI": "Most stable live mode for grounded financial answers.",
    "Fine-Tuned": "Domain-adapted banking model path for specialized tone and phrasing.",
    "Auto": "Selects the strongest grounded answer across available model paths.",
}
"""

REPLACE_2 = """
MODEL_DESCRIPTIONS = {
    "OpenAI": "Most stable live mode for grounded financial answers.",
    "Fine-Tuned": "Domain-adapted banking model path for specialized tone and phrasing.",
    "Auto": "Selects the strongest grounded answer across available model paths.",
    "Agentic Workspace": (
        "🤖 True autonomous agent — plans, selects tools, executes step-by-step, "
        "verifies with an LLM judge, and retries when evidence is weak. "
        "Best for complex multi-step questions."
    ),
}

# ── Mode name constant (use this string everywhere — no typos) ────────────────
AGENTIC_MODE = "Agentic Workspace"
ALL_MODES = ["OpenAI", "Fine-Tuned", "Auto", AGENTIC_MODE]
"""


# ══════════════════════════════════════════════════════════════════════════════
# PATCH 3 — Sidebar radio (add Agentic Workspace)
# ══════════════════════════════════════════════════════════════════════════════

FIND_3 = """
        model_mode = st.radio(
            "Model mode",
            ["OpenAI", "Fine-Tuned", "Auto"],
            index=["OpenAI", "Fine-Tuned", "Auto"].index(st.session_state.model_mode),
            horizontal=True,
            label_visibility="collapsed",
            key="model_mode_selector",
        )
"""

REPLACE_3 = """
        model_mode = st.radio(
            "Model mode",
            ALL_MODES,
            index=(
                ALL_MODES.index(st.session_state.model_mode)
                if st.session_state.model_mode in ALL_MODES
                else 0
            ),
            horizontal=True,
            label_visibility="collapsed",
            key="model_mode_selector",
        )
"""


# ══════════════════════════════════════════════════════════════════════════════
# PATCH 4 — Composer selectbox (add Agentic Workspace)
# ══════════════════════════════════════════════════════════════════════════════

FIND_4 = """
        composer_mode = st.selectbox(
            "Composer model",
            ["OpenAI", "Fine-Tuned", "Auto"],
            index=["OpenAI", "Fine-Tuned", "Auto"].index(st.session_state.model_mode),
            label_visibility="collapsed",
            key="composer_model_mode",
        )
"""

REPLACE_4 = """
        composer_mode = st.selectbox(
            "Composer model",
            ALL_MODES,
            index=(
                ALL_MODES.index(st.session_state.model_mode)
                if st.session_state.model_mode in ALL_MODES
                else 0
            ),
            label_visibility="collapsed",
            key="composer_model_mode",
        )
"""


# ══════════════════════════════════════════════════════════════════════════════
# PATCH 5 — _run_selected_model() — FIX: pass retriever, use AGENTIC_MODE name
# ══════════════════════════════════════════════════════════════════════════════

FIND_5 = """
def _run_selected_model(question: str, retrieval: dict, model_mode: str) -> dict:
    uploaded_images = st.session_state.get("uploaded_images", [])
    if model_mode == "OpenAI":
        return generate_openai_response(question, retrieval, uploaded_images=uploaded_images)
    if model_mode == "Fine-Tuned":
        return generate_finetuned_response(question, retrieval, uploaded_images=uploaded_images)
    return run_auto_mode(question, retrieval, uploaded_images=uploaded_images)
"""

REPLACE_5 = """
def _run_selected_model(question: str, retrieval: dict, model_mode: str) -> dict:
    uploaded_images = st.session_state.get("uploaded_images", [])

    if model_mode == AGENTIC_MODE:
        # ── Collect inputs ────────────────────────────────────────────────────
        uploaded_docs  = st.session_state.get("uploaded_docs", [])
        chat_history   = st.session_state.get("messages", [])

        # ── Pass the real retriever so the agent uses FAISS/BM25 knowledge base
        # retrieval["base_index"] holds the FAISS index built at startup
        # If your retriever is a module-level object, import it directly instead
        retriever_obj  = st.session_state.get("retriever_obj", None)

        agent_result = run_agentic_workflow(
            user_query     = question,
            uploaded_files = uploaded_docs,
            chat_history   = chat_history,
            retriever      = retriever_obj,   # ← FIXED: real FAISS retriever passed
        )

        # Store for trace UI rendering
        st.session_state["last_agent_result"] = agent_result

        # Normalise to the standard result shape expected by the rest of the runtime
        return {
            "answer":       agent_result.get("answer", ""),
            "backend":      AGENTIC_MODE,
            "latency_ms":   agent_result.get("latency_ms", 0),
            "confidence":   agent_result.get("confidence", "Low"),
            "score":        {"total": 0.0},
            "available":    True,
            "route_reason": "Tools: " + ", ".join(agent_result.get("tools_used", [])),
            "agent_result": agent_result,
        }

    if model_mode == "OpenAI":
        return generate_openai_response(question, retrieval, uploaded_images=uploaded_images)
    if model_mode == "Fine-Tuned":
        return generate_finetuned_response(question, retrieval, uploaded_images=uploaded_images)
    return run_auto_mode(question, retrieval, uploaded_images=uploaded_images)
"""


# ══════════════════════════════════════════════════════════════════════════════
# PATCH 6 — Cache retriever object in session_state at startup
# ══════════════════════════════════════════════════════════════════════════════
# Add this block AFTER `base_index = get_base_index()` in run_product_runtime()

FIND_6 = """
    base_index = get_base_index()
    base_doc_count = len(load_base_documents())
"""

REPLACE_6 = """
    base_index = get_base_index()
    base_doc_count = len(load_base_documents())

    # ── Cache retriever in session_state so Agentic Workspace can access it ──
    # This wraps the base_index so it can be passed to AgenticRuntime
    if "retriever_obj" not in st.session_state or st.session_state.retriever_obj is None:
        class _RetrieverProxy:
            \"\"\"Lightweight proxy so AgenticRuntime can call retrieve_shared_context.\"\"\"
            def __init__(self, b_index, u_index=None):
                self.base_index  = b_index
                self.upload_index = u_index
        st.session_state.retriever_obj = _RetrieverProxy(base_index)

    # Update upload index whenever it changes
    if st.session_state.get("upload_index") is not None:
        st.session_state.retriever_obj.upload_index = st.session_state.upload_index
"""


# ══════════════════════════════════════════════════════════════════════════════
# PATCH 7 — Render agent trace after assistant message
# ══════════════════════════════════════════════════════════════════════════════

FIND_7 = """
    with st.chat_message("assistant"):
        _stream_answer_preview(assistant_message["answer"])
        render_assistant_message(
            assistant_message,
            message_key=f"latest-{len(st.session_state.messages)}",
            simplified_answers=accessibility.simplified_answers,
            show_source_cards=show_source_cards,
            show_auto_comparison=show_auto_comparison,
        )
"""

REPLACE_7 = """
    with st.chat_message("assistant"):
        _stream_answer_preview(assistant_message["answer"])
        render_assistant_message(
            assistant_message,
            message_key=f"latest-{len(st.session_state.messages)}",
            simplified_answers=accessibility.simplified_answers,
            show_source_cards=show_source_cards,
            show_auto_comparison=show_auto_comparison,
        )
        # Render Agentic Workspace trace panel if agent mode was used
        agent_result = result.get("agent_result")
        if agent_result:
            render_agent_trace(agent_result)
            render_portfolio_table(agent_result)
"""


# ══════════════════════════════════════════════════════════════════════════════
# VERIFICATION CHECKLIST — run this after applying all patches
# ══════════════════════════════════════════════════════════════════════════════

VERIFICATION_CHECKLIST = """
After applying all 7 patches:

□ 1. Search "Agentic" in product_runtime.py — should only appear as "Agentic Workspace"
     (no bare "Agentic" string in mode lists or comparisons)

□ 2. Search "run_agentic_workflow" — should appear exactly once, with retriever= argument

□ 3. In sidebar radio: options list should be ALL_MODES (4 items)

□ 4. In composer selectbox: options list should be ALL_MODES (4 items)

□ 5. retriever_obj should be set in session_state at startup

□ 6. Test: switch to "Agentic Workspace" in selector — should not 404

□ 7. Test question 5 with no prior history:
     "I have $500,000 to invest..."
     Expected: agent asks 3 clarifying questions, NO portfolio table

□ 8. Confirm trace panel shows:
     - 🧠 Intent analysis
     - 🔧 risk_profile_tool
     - 📋 Result: risk_profile_tool  (enough_information: false)
     - ✅ Agent complete
"""
