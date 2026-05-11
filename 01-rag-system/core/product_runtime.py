from __future__ import annotations

import json
from pathlib import Path
import time
from typing import Any
from datetime import datetime, timezone
from uuid import uuid4

import streamlit as st

from core.agentic_runtime import AgenticRuntime
from core.retriever import get_base_index, retrieve_shared_context
from core.utils import detect_input_language, list_base_knowledge_files
from features.accessibility import apply_accessibility_styles, render_accessibility_controls
from features.file_upload import render_document_uploads, render_image_uploads
from features.product_ui import (
    enforce_composer_pin,
    inject_premium_css,
    render_about_section,
    render_assistant_message,
    render_assistant_thinking,
    render_footer,
    render_header,
    render_session_insights,
    render_sidebar_brand,
    render_sidebar_summary,
    render_stack_section,
    render_starter_prompts,
    render_user_message,
    render_welcome_card,
)
from features.voice_controls import render_voice_input_preview
from models.auto_router import run_auto_mode
from models.autonomous_agent import run_autonomous_agent
from models.finetuned_mode import generate_finetuned_response
from models.openai_mode import generate_openai_response

MODEL_MODES = ["Autonomous Max", "OpenAI", "Fine-Tuned", "Auto", "Agentic Workspace"]

MODEL_DESCRIPTIONS = {
    "Autonomous Max": "Fully autonomous supervisor mode: resolves missing inputs with explicit assumptions and continues execution.",
    "OpenAI": "Most stable live mode for grounded financial answers.",
    "Fine-Tuned": "Domain-adapted banking model path for specialized tone and phrasing.",
    "Auto": "Selects the strongest grounded answer across available model paths.",
    "Agentic Workspace": "Tool-calling agent that plans, retrieves, analyzes, verifies, and answers with execution trace.",
}
AGENT_MEMORY_PATH = Path(__file__).resolve().parent.parent / "data" / "agent_memory.json"
AUTONOMOUS_QUEUE_PATH = Path(__file__).resolve().parent.parent / "data" / "autonomous_queue.json"
AUTONOMOUS_AUDIT_PATH = Path(__file__).resolve().parent.parent / "data" / "autonomous_audit_log.jsonl"


def _chat_title(messages: list[dict[str, Any]]) -> str:
    for message in messages:
        if message.get("role") == "user" and message.get("content"):
            title = " ".join(str(message["content"]).split())
            return title[:42] + ("..." if len(title) > 42 else "")
    return "New chat"


def _get_active_chat() -> dict[str, Any]:
    for chat in st.session_state.chat_threads:
        if chat["id"] == st.session_state.active_chat_id:
            return chat
    fallback = st.session_state.chat_threads[0]
    st.session_state.active_chat_id = fallback["id"]
    return fallback


def _save_active_chat() -> None:
    chat = _get_active_chat()
    chat["messages"] = [dict(m) for m in st.session_state.messages]
    chat["title"] = _chat_title(chat["messages"])


def _load_active_chat() -> None:
    st.session_state.messages = [dict(m) for m in _get_active_chat()["messages"]]


def _create_new_chat() -> None:
    _save_active_chat()
    new_id = f"chat-{int(time.time() * 1000)}"
    st.session_state.chat_threads.insert(0, {"id": new_id, "title": "New chat", "messages": []})
    st.session_state.active_chat_id = new_id
    st.session_state.messages = []


def _ensure_state() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "chat_threads" not in st.session_state:
        initial = [dict(m) for m in st.session_state.messages]
        st.session_state.chat_threads = [{"id": "chat-1", "title": _chat_title(initial), "messages": initial}]
        st.session_state.active_chat_id = "chat-1"
    elif "active_chat_id" not in st.session_state:
        st.session_state.active_chat_id = st.session_state.chat_threads[0]["id"]
    _load_active_chat()

    defaults = {
        "upload_signature": "",
        "upload_index": None,
        "upload_doc_count": 0,
        "upload_chunk_count": 0,
        "uploaded_docs": [],
        "uploaded_images": [],
        "model_mode": "Autonomous Max",
        "pending_question": "",
        "last_voice_lang": "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v
    if st.session_state.model_mode == "Autonomous Agent":
        st.session_state.model_mode = "Agentic Workspace"
    if st.session_state.model_mode not in MODEL_MODES:
        st.session_state.model_mode = "Autonomous Max"
    if "agent_memory" not in st.session_state:
        st.session_state.agent_memory = _load_agent_memory()
    if "autonomous_queue" not in st.session_state:
        st.session_state.autonomous_queue = _load_autonomous_queue()
    if "autonomous_loop_enabled" not in st.session_state:
        st.session_state.autonomous_loop_enabled = False


def _load_agent_memory() -> list[dict[str, Any]]:
    try:
        if AGENT_MEMORY_PATH.exists():
            return json.loads(AGENT_MEMORY_PATH.read_text(encoding="utf-8"))
    except Exception:
        return []
    return []


def _persist_agent_memory(memory: list[dict[str, Any]]) -> None:
    try:
        AGENT_MEMORY_PATH.parent.mkdir(parents=True, exist_ok=True)
        AGENT_MEMORY_PATH.write_text(json.dumps(memory[-250:], ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def _load_autonomous_queue() -> list[dict[str, Any]]:
    try:
        if AUTONOMOUS_QUEUE_PATH.exists():
            data = json.loads(AUTONOMOUS_QUEUE_PATH.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return data
    except Exception:
        return []
    return []


def _persist_autonomous_queue(queue: list[dict[str, Any]]) -> None:
    try:
        AUTONOMOUS_QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)
        AUTONOMOUS_QUEUE_PATH.write_text(
            json.dumps(queue[-500:], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception:
        pass


def _append_autonomous_audit(event: dict[str, Any]) -> None:
    try:
        AUTONOMOUS_AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
        payload = dict(event)
        payload["logged_at_utc"] = datetime.now(timezone.utc).isoformat()
        with AUTONOMOUS_AUDIT_PATH.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _policy_decision_from_result(question: str, result: dict[str, Any]) -> str:
    q = question.lower()
    triggers = {"sanction", "ofac", "iran", "structuring", "smurf", "pep", "aml", "sar"}
    if any(t in q for t in triggers):
        return "escalation_required"
    confidence = str(result.get("confidence", "Moderate"))
    if confidence == "Low":
        return "human_review_recommended"
    if result.get("requires_clarification"):
        return "needs_more_input"
    return "auto_completed"


def _response_profile(question: str) -> str:
    q = question.lower().strip()
    direct_hints = ("what is", "define", "meaning", "who is", "when is", "quick", "short")
    if len(q.split()) <= 10 or any(h in q for h in direct_hints):
        return "direct"
    return "detailed"


def _llm_text_call(prompt: str, retrieval: dict, response_language: str, response_profile: str) -> str:
    result = generate_openai_response(
        prompt,
        retrieval,
        uploaded_images=[],
        response_language=response_language,
        response_profile=response_profile,
    )
    return result.get("answer", "")


def _run_selected_model(question: str, retrieval: dict, mode: str) -> dict:
    images = st.session_state.get("uploaded_images", [])
    response_language = (st.session_state.get("last_voice_lang") or "").strip() or detect_input_language(question)
    response_profile = _response_profile(question)
    if mode == "OpenAI":
        return generate_openai_response(
            question,
            retrieval,
            uploaded_images=images,
            response_language=response_language,
            response_profile=response_profile,
        )
    if mode == "Fine-Tuned":
        return generate_finetuned_response(
            question,
            retrieval,
            uploaded_images=images,
            response_language=response_language,
            response_profile=response_profile,
        )
    if mode == "Autonomous Max":
        agent = AgenticRuntime(
            retriever=lambda q, top_k=5: retrieve_shared_context(
                q, get_base_index(), st.session_state.upload_index
            ),
            uploaded_docs=st.session_state.get("uploaded_docs", []),
        )
        result = agent.run_fully_autonomous(
            user_query=question,
            chat_history=st.session_state.messages,
        )
        trace_steps = result.get("agent_steps") or result.get("trace") or []
        st.session_state.agent_memory.append({"question": question, "steps": trace_steps})
        _persist_agent_memory(st.session_state.agent_memory)
        return result

    if mode == "Agentic Workspace":
        agent = AgenticRuntime(
            retriever=lambda q, top_k=5: retrieve_shared_context(
                q, get_base_index(), st.session_state.upload_index
            ),
            uploaded_docs=st.session_state.get("uploaded_docs", []),
        )
        result = agent.run(
            user_query=question,
            chat_history=st.session_state.messages,
        )
        trace_steps = result.get("agent_steps") or result.get("trace") or []
        st.session_state.agent_memory.append({"question": question, "steps": trace_steps})
        _persist_agent_memory(st.session_state.agent_memory)
        return result

    if mode == "Autonomous Agent":
        result = run_autonomous_agent(
            question=question,
            retrieval=retrieval,
            llm_call=lambda p: _llm_text_call(p, retrieval, response_language, response_profile),
            memory=st.session_state.agent_memory,
            response_language=response_language,
            retriever_call=lambda q: retrieve_shared_context(q, get_base_index(), st.session_state.upload_index),
            response_profile=response_profile,
        )
        st.session_state.agent_memory.append({"question": question, "steps": result.get("agent_steps", [])})
        _persist_agent_memory(st.session_state.agent_memory)
        return result
    return run_auto_mode(question, retrieval, uploaded_images=images)


def _run_autonomous_task(task: dict[str, Any], base_index) -> dict[str, Any]:
    question = str(task.get("question", "")).strip()
    if not question:
        return {"status": "skipped", "reason": "empty_question"}
    retrieval = retrieve_shared_context(question, base_index, st.session_state.upload_index)
    result = _run_selected_model(question, retrieval, "Autonomous Max")
    policy_decision = _policy_decision_from_result(question, result)
    _append_autonomous_audit(
        {
            "task_id": task.get("id"),
            "task_label": task.get("label"),
            "question": question,
            "mode": "Autonomous Max",
            "policy_decision": policy_decision,
            "confidence": result.get("confidence"),
            "latency_ms": result.get("latency_ms"),
            "tools_used": result.get("tools_used", []),
            "requires_clarification": result.get("requires_clarification", False),
        }
    )
    return {
        "status": "completed",
        "result": result,
        "retrieval": retrieval,
        "policy_decision": policy_decision,
    }


def run_product_runtime() -> None:
    st.set_page_config(page_title="Banking & Finance Copilot", page_icon="🌍", layout="wide", initial_sidebar_state="expanded")
    _ensure_state()

    inject_premium_css()

    # Lazy-load retrieval resources so homepage paints immediately.
    base_index = None
    base_doc_count = len(list_base_knowledge_files())

    show_source_cards = True
    show_auto_comparison = False
    voice_transcript = ""
    question = ""
    submitted = False

    with st.sidebar:
        st.markdown('<div class="custom-sidebar-anchor"></div>', unsafe_allow_html=True)
        render_sidebar_brand()

        if st.button("+ New Chat", use_container_width=True, key="new_chat_btn"):
            _create_new_chat()
            st.rerun()

        st.markdown('<div class="sidebar-section-label">Recent Chats</div>', unsafe_allow_html=True)
        chat_ids = [c["id"] for c in st.session_state.chat_threads]
        active_index = chat_ids.index(st.session_state.active_chat_id) if st.session_state.active_chat_id in chat_ids else 0
        selected_id = st.radio(
            "Chat history",
            options=chat_ids,
            index=active_index,
            label_visibility="collapsed",
            format_func=lambda cid: next(c["title"] for c in st.session_state.chat_threads if c["id"] == cid),
            key="chat_history_selector",
        )
        if selected_id != st.session_state.active_chat_id:
            _save_active_chat()
            st.session_state.active_chat_id = selected_id
            _load_active_chat()
            st.rerun()

        with st.expander("Workspace", expanded=True):
            mode = st.radio(
                "Model mode",
                MODEL_MODES,
                index=MODEL_MODES.index(st.session_state.model_mode),
                horizontal=True,
                label_visibility="collapsed",
                key="model_mode_selector",
            )
            st.session_state.model_mode = mode
            st.session_state.composer_model_mode = mode
            st.caption(MODEL_DESCRIPTIONS[mode])
            st.markdown('<div class="sidebar-section-label">Autonomous Ops</div>', unsafe_allow_html=True)
            st.session_state.autonomous_loop_enabled = st.toggle(
                "Autonomous background execution",
                value=bool(st.session_state.autonomous_loop_enabled),
                key="autonomous_loop_toggle",
            )
            task_label = st.text_input(
                "Task label",
                value="",
                placeholder="Example: Daily compliance sweep",
                key="autonomous_task_label",
            )
            task_question = st.text_area(
                "Autonomous task prompt",
                value="",
                placeholder="Describe the task the autonomous agent should run.",
                height=80,
                key="autonomous_task_prompt",
            )
            if st.button("Queue autonomous task", use_container_width=True, key="queue_autonomous_task_btn"):
                if task_question.strip():
                    st.session_state.autonomous_queue.append(
                        {
                            "id": f"task-{uuid4().hex[:12]}",
                            "label": task_label.strip() or "Autonomous Task",
                            "question": task_question.strip(),
                            "status": "pending",
                            "created_at_utc": datetime.now(timezone.utc).isoformat(),
                        }
                    )
                    _persist_autonomous_queue(st.session_state.autonomous_queue)
                    st.success("Autonomous task queued.")
                else:
                    st.warning("Add a task prompt before queueing.")
            pending_count = sum(1 for t in st.session_state.autonomous_queue if t.get("status") == "pending")
            st.caption(f"Pending autonomous tasks: {pending_count}")
            accessibility = render_accessibility_controls()
            show_source_cards = st.toggle("Show source cards", value=False)
            show_auto_comparison = st.toggle("Auto mode comparison", value=False)
            st.markdown('<div class="sidebar-section-label">Knowledge State</div>', unsafe_allow_html=True)
            render_sidebar_summary(base_doc_count, st.session_state.upload_doc_count, st.session_state.upload_chunk_count)
            st.markdown('<div class="sidebar-section-label">Session Metrics</div>', unsafe_allow_html=True)
            render_session_insights(st.session_state.messages)

    apply_accessibility_styles(accessibility)

    render_header()

    if not st.session_state.messages:
        render_welcome_card()
        starter_prompt = render_starter_prompts()
        render_about_section()
        render_stack_section()
    else:
        starter_prompt = None

    for i, msg in enumerate(st.session_state.messages):
        if msg.get("role") == "user":
            render_user_message(str(msg.get("content", "")))
        else:
            render_assistant_message(
                msg,
                message_key=f"history-{i}",
                simplified_answers=accessibility.simplified_answers,
                show_source_cards=show_source_cards,
                show_auto_comparison=show_auto_comparison,
            )

    if (
        st.session_state.get("autonomous_loop_enabled")
        and not st.session_state.get("pending_question")
        and st.session_state.get("autonomous_queue")
    ):
        pending_idx = next(
            (idx for idx, task in enumerate(st.session_state.autonomous_queue) if task.get("status") == "pending"),
            None,
        )
        if pending_idx is not None:
            task = st.session_state.autonomous_queue[pending_idx]
            task["status"] = "running"
            task["started_at_utc"] = datetime.now(timezone.utc).isoformat()
            _persist_autonomous_queue(st.session_state.autonomous_queue)
            if base_index is None:
                base_index = get_base_index()
            render_user_message(f"[Autonomous Task] {task.get('label', 'Task')}: {task.get('question', '')}")
            render_assistant_thinking()
            task_outcome = _run_autonomous_task(task, base_index)
            if task_outcome.get("status") == "completed":
                result = task_outcome["result"]
                retrieval = task_outcome["retrieval"]
                policy_decision = task_outcome["policy_decision"]
                assistant_msg = {
                    "role": "assistant",
                    "answer": result.get("answer", ""),
                    "backend": result.get("backend", "Autonomous Max"),
                    "latency_ms": result.get("latency_ms", 0),
                    "retrieved_chunks": retrieval.get("retrieved_chunks", 0),
                    "sources": retrieval.get("sources", []),
                    "source_cards": retrieval.get("source_cards", []),
                    "confidence": result.get("confidence", "Moderate"),
                    "comparison": result.get("comparison"),
                    "route_reason": result.get("route_reason"),
                    "selection_reason": f"Autonomous task execution ({policy_decision}).",
                    "candidate_scores": result.get("candidate_scores"),
                    "agent_steps": result.get("agent_steps") or result.get("trace") or [],
                    "agent_observations": result.get("agent_observations") or result.get("trace") or [],
                    "voice_lang_hint": result.get("language", detect_input_language(task.get("question", ""))),
                }
                st.session_state.messages.append({"role": "user", "content": f"[Autonomous Task] {task.get('question', '')}"})
                st.session_state.messages.append(assistant_msg)
                task["status"] = "completed"
                task["completed_at_utc"] = datetime.now(timezone.utc).isoformat()
                task["policy_decision"] = policy_decision
            else:
                task["status"] = "failed"
                task["failure_reason"] = task_outcome.get("reason", "unknown")
                task["completed_at_utc"] = datetime.now(timezone.utc).isoformat()
            _persist_autonomous_queue(st.session_state.autonomous_queue)
            _save_active_chat()
            st.rerun()

    # Process deferred generation so the user message appears in history above composer.
    pending_question = st.session_state.get("pending_question")
    if pending_question:
        if base_index is None:
            base_index = get_base_index()
        render_assistant_thinking()
        retrieval = retrieve_shared_context(pending_question, base_index, st.session_state.upload_index)
        result = _run_selected_model(pending_question, retrieval, st.session_state.model_mode)
        if result.get("retrieval_override"):
            retrieval = result["retrieval_override"]

        assistant_msg = {
            "role": "assistant",
            "answer": result.get("answer", ""),
            "backend": result.get("backend", st.session_state.model_mode),
            "latency_ms": result.get("latency_ms", 0),
            "retrieved_chunks": retrieval.get("retrieved_chunks", 0),
            "sources": retrieval.get("sources", []),
            "source_cards": retrieval.get("source_cards", []),
            "confidence": result.get("confidence", "Moderate"),
            "comparison": result.get("comparison"),
            "route_reason": result.get("route_reason"),
            "selection_reason": result.get("selection_reason"),
            "candidate_scores": result.get("candidate_scores"),
            "agent_steps": result.get("agent_steps") or result.get("trace") or [],
            "agent_observations": result.get("agent_observations") or result.get("trace") or [],
            "voice_lang_hint": result.get("language", detect_input_language(pending_question)),
        }
        st.session_state.messages.append(assistant_msg)
        _save_active_chat()
        st.session_state.pending_question = ""
        st.rerun()

    st.markdown("<div class='composer-shell-static'>", unsafe_allow_html=True)
    with st.form("composer_form", clear_on_submit=True, border=False):
        st.markdown("<div class='composer-marker'></div>", unsafe_allow_html=True)
        st.markdown("<div class='composer-row'>", unsafe_allow_html=True)
        c1, c2, c3, c4, c5 = st.columns([0.8, 1.1, 3.6, 0.9, 0.5])
        with c1:
            with st.popover("+", use_container_width=True):
                render_document_uploads()
                render_image_uploads()
        with c2:
            composer_mode = st.selectbox(
                "Composer model",
                MODEL_MODES,
                index=MODEL_MODES.index(st.session_state.model_mode),
                label_visibility="collapsed",
                key="composer_model_mode",
            )
            st.session_state.model_mode = composer_mode
        with c3:
            question = st.text_input(
                "Ask banking question",
                placeholder="Ask anything about banking, finance, regulations, or compliance...",
                label_visibility="collapsed",
                key="composer_text_input_inline",
            )
        with c4:
            with st.popover("🎤", use_container_width=True):
                voice_transcript, _ = render_voice_input_preview()
        with c5:
            submitted = st.form_submit_button("↑", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    enforce_composer_pin()
    if not submitted and not voice_transcript and not starter_prompt:
        render_footer()
        return

    if not question and voice_transcript:
        question = voice_transcript
    if not question and starter_prompt:
        question = starter_prompt
    if not question:
        render_footer()
        return

    # Guarantee submit uses composer-selected mode (avoids stale sidebar/composer mismatch).
    st.session_state.model_mode = st.session_state.get("composer_model_mode", st.session_state.model_mode)
    st.session_state.messages.append({"role": "user", "content": question})
    _save_active_chat()
    st.session_state.pending_question = question
    st.rerun()
