from __future__ import annotations

import ast
import json
import os
import re
import time
from datetime import datetime, timezone
from typing import Any, Callable

MAX_AGENT_STEPS = max(2, int(os.environ.get("AUTONOMOUS_MAX_STEPS", "4")))


def _safe_json_loads(text: str) -> dict[str, Any]:
    try:
        start = text.find("{")
        end = text.rfind("}") + 1
        return json.loads(text[start:end])
    except Exception:
        return {
            "thought": "Fallback to final grounded answer.",
            "action": "finish",
            "input": "",
        }


def _planner_prompt(
    question: str,
    memory: list[dict[str, Any]],
    observations: list[dict[str, Any]],
    weak_retrieval: bool,
) -> str:
    return f"""
You are a bounded autonomous Banking & Finance AI Agent.

Goal:
Solve the user request with tool-use + retrieved evidence.

Question:
{question}

Weak retrieval now: {weak_retrieval}
Recent memory:
{memory[-3:] if memory else []}
Observations:
{observations[-4:] if observations else []}

Available actions (choose ONE):
- retrieve: retrieve evidence for the current query
- retrieve_retry: rewrite/refine query then retrieve again
- analyze: reason over current evidence
- compare: compare evidence/options
- calculate: do deterministic numeric calculation
- date_check: check date/freshness logic
- self_check: verify groundedness/completeness
- finish: produce final answer

Return ONLY strict JSON:
{{
  "thought": "why this step is needed",
  "action": "retrieve|retrieve_retry|analyze|compare|calculate|date_check|self_check|finish",
  "input": "short action input"
}}
"""


def _final_prompt(
    question: str,
    steps: list[dict[str, Any]],
    observations: list[dict[str, Any]],
    retrieval: dict[str, Any],
    response_language: str,
    response_profile: str,
) -> str:
    profile_rule = {
        "direct": "Keep answer concise and direct first.",
        "detailed": "Provide detailed explanation with practical context.",
        "balanced": "Provide clear moderate detail.",
    }.get(response_profile, "Provide clear moderate detail.")
    return f"""
You are a Banking & Finance Autonomous Agentic AI Copilot.

User question:
{question}

Execution steps:
{steps}

Tool observations:
{observations}

Retrieved context:
{retrieval.get("context", "")}

Sources:
{retrieval.get("sources", [])}

Write final answer in: {response_language}

Rules:
- Keep grounded to retrieved evidence first.
- If evidence is weak, state the gap clearly.
- If user asked direct fact, answer directly first.
- Then provide concise key points.
- Do not claim legal or compliance authority.
- {profile_rule}
"""


def _self_check_prompt(question: str, draft: str, retrieval: dict[str, Any]) -> str:
    return f"""
Check the answer quality.

Question:
{question}

Draft:
{draft}

Sources:
{retrieval.get("sources", [])}

Context:
{retrieval.get("context", "")}

Return:
- Grounded: Yes/Partial/No
- Missing:
- Correction:
"""


def _safe_math(expr: str) -> str:
    allowed = set("0123456789+-*/(). %")
    cleaned = "".join(ch for ch in expr if ch in allowed)
    if not cleaned.strip():
        return "No valid numeric expression found."
    try:
        tree = ast.parse(cleaned, mode="eval")
        for node in ast.walk(tree):
            if not isinstance(
                node,
                (
                    ast.Expression,
                    ast.BinOp,
                    ast.UnaryOp,
                    ast.Constant,
                    ast.Add,
                    ast.Sub,
                    ast.Mult,
                    ast.Div,
                    ast.Mod,
                    ast.Pow,
                    ast.USub,
                    ast.UAdd,
                    ast.FloorDiv,
                ),
            ):
                return "Expression contains unsupported operations."
        value = eval(compile(tree, "<math>", "eval"), {"__builtins__": {}})
        return f"{value}"
    except Exception:
        return "Could not evaluate expression safely."


def _date_check(input_text: str) -> str:
    now = datetime.now(timezone.utc)
    found = re.findall(r"\d{4}-\d{2}-\d{2}", input_text or "")
    if not found:
        return f"No ISO date found. Current UTC date: {now.date().isoformat()}."
    latest = max(found)
    return f"Detected date(s): {found}. Latest date: {latest}. Current UTC date: {now.date().isoformat()}."


def _execute_tool(
    action: str,
    tool_input: str,
    question: str,
    retrieval: dict[str, Any],
    llm_call: Callable[[str], str],
    retriever_call: Callable[[str], dict[str, Any]] | None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    # returns (observation, possibly_updated_retrieval)
    if action == "retrieve":
        if retriever_call:
            updated = retriever_call(tool_input or question)
        else:
            updated = retrieval
        return (
            {
                "tool": "retrieve",
                "input": tool_input or question,
                "result": {
                    "retrieved_chunks": updated.get("retrieved_chunks", 0),
                    "sources": updated.get("sources", []),
                    "weak_retrieval": updated.get("weak_retrieval", False),
                    "context_preview": updated.get("context", "")[:700],
                },
            },
            updated,
        )

    if action == "retrieve_retry":
        rewrite_prompt = f"Rewrite this query for better retrieval in banking/compliance docs:\n{tool_input or question}\nReturn one line."
        revised = (llm_call(rewrite_prompt) or "").strip().splitlines()[0][:240]
        updated = retriever_call(revised) if retriever_call else retrieval
        return (
            {
                "tool": "retrieve_retry",
                "input": revised,
                "result": {
                    "retrieved_chunks": updated.get("retrieved_chunks", 0),
                    "sources": updated.get("sources", []),
                    "weak_retrieval": updated.get("weak_retrieval", False),
                    "context_preview": updated.get("context", "")[:700],
                },
            },
            updated,
        )

    if action == "analyze":
        prompt = f"Analyze the banking evidence briefly.\nQuestion: {question}\nEvidence:\n{retrieval.get('context','')}\nReturn concise findings."
        return ({"tool": "analyze", "input": tool_input, "result": llm_call(prompt)}, retrieval)

    if action == "compare":
        prompt = f"Compare possible answer paths from sources.\nQuestion: {question}\nSources: {retrieval.get('sources',[])}\nReturn concise comparison."
        return ({"tool": "compare", "input": tool_input, "result": llm_call(prompt)}, retrieval)

    if action == "calculate":
        return ({"tool": "calculate", "input": tool_input, "result": _safe_math(tool_input or question)}, retrieval)

    if action == "date_check":
        return ({"tool": "date_check", "input": tool_input, "result": _date_check(tool_input or question)}, retrieval)

    if action == "self_check":
        draft = llm_call(_final_prompt(question, [], [], retrieval, "same language as user", response_profile))
        check = llm_call(_self_check_prompt(question, draft, retrieval))
        return ({"tool": "self_check", "input": tool_input, "result": check}, retrieval)

    return ({"tool": "finish", "input": tool_input, "result": "Agent stopped with current evidence."}, retrieval)


def run_autonomous_agent(
    question: str,
    retrieval: dict[str, Any],
    llm_call: Callable[[str], str],
    memory: list[dict[str, Any]] | None = None,
    response_language: str = "same language as the user question",
    retriever_call: Callable[[str], dict[str, Any]] | None = None,
    response_profile: str = "balanced",
) -> dict[str, Any]:
    start = time.perf_counter()
    memory = memory or []

    steps: list[dict[str, Any]] = []
    observations: list[dict[str, Any]] = []
    current_retrieval = dict(retrieval)

    for step_index in range(MAX_AGENT_STEPS):
        plan = _safe_json_loads(
            llm_call(
                _planner_prompt(
                    question=question,
                    memory=memory,
                    observations=observations,
                    weak_retrieval=bool(current_retrieval.get("weak_retrieval")),
                )
            )
        )
        action = str(plan.get("action", "finish")).strip().lower()
        thought = str(plan.get("thought", "")).strip()
        tool_input = str(plan.get("input", "")).strip()

        step = {"step": step_index + 1, "thought": thought, "action": action, "input": tool_input}
        steps.append(step)

        if action == "finish":
            break

        obs, updated_retrieval = _execute_tool(
            action=action,
            tool_input=tool_input,
            question=question,
            retrieval=current_retrieval,
            llm_call=llm_call,
            retriever_call=retriever_call,
        )
        observations.append(obs)
        current_retrieval = updated_retrieval

    final_answer = llm_call(
        _final_prompt(
            question=question,
            steps=steps,
            observations=observations,
            retrieval=current_retrieval,
            response_language=response_language,
            response_profile=response_profile,
        )
    )

    latency_ms = round((time.perf_counter() - start) * 1000)
    confidence = "High"
    if current_retrieval.get("weak_retrieval"):
        confidence = "Medium"
    if not current_retrieval.get("sources"):
        confidence = "Low"

    return {
        "answer": final_answer,
        "backend": "Autonomous Agentic AI",
        "model_name": "autonomous-agentic-rag-v2",
        "latency_ms": latency_ms,
        "confidence": confidence,
        "available": True,
        "agent_steps": steps,
        "agent_observations": observations,
        "route_reason": "autonomous_agentic_loop",
        "selection_reason": "Planner -> tools -> observation -> final grounded answer.",
        "language": response_language,
        "retrieval_override": current_retrieval,
    }
