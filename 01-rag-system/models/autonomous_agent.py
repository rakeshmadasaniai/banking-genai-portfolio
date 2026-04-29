from __future__ import annotations

import json
import time
from typing import Any, Callable

MAX_AGENT_STEPS = 4


def _safe_json_loads(text: str) -> dict[str, Any]:
    try:
        start = text.find("{")
        end = text.rfind("}") + 1
        return json.loads(text[start:end])
    except Exception:
        return {
            "thought": "Fallback: answer using retrieved evidence.",
            "action": "finish",
            "input": "",
        }


def _agent_planner_prompt(question: str, memory: list[dict[str, Any]], observations: list[dict[str, Any]]) -> str:
    return f"""
You are a bounded autonomous Banking & Finance AI Agent.

Goal:
Answer the user using multi-step reasoning, tool execution, and retrieved evidence.

User question:
{question}

Recent memory:
{memory[-3:] if memory else []}

Observations:
{observations}

Choose ONE next action:
- retrieve: search banking/compliance knowledge
- analyze: reason over retrieved evidence
- compare: compare sources or model behavior
- self_check: verify grounding and completeness
- finish: stop and produce final answer

Return ONLY valid JSON:
{{
  "thought": "why this step is needed",
  "action": "retrieve | analyze | compare | self_check | finish",
  "input": "short tool input"
}}
"""


def _final_answer_prompt(
    question: str,
    agent_steps: list[dict[str, Any]],
    observations: list[dict[str, Any]],
    retrieval: dict[str, Any],
) -> str:
    return f"""
You are a Banking & Finance Autonomous Agentic AI Copilot.

User question:
{question}

Agent steps:
{agent_steps}

Tool observations:
{observations}

Retrieved context:
{retrieval.get("context", "")}

Sources:
{retrieval.get("sources", [])}

Write the final answer.

Rules:
- Use retrieved evidence first.
- Be clear and professional.
- Do not claim legal, investment, or compliance authority.
- If evidence is weak, say what is missing.
- Include these sections:
  1. Answer
  2. Agentic Execution Trace
  3. Evidence Used
  4. Confidence
"""


def _self_check_prompt(question: str, draft: str, retrieval: dict[str, Any]) -> str:
    return f"""
Check whether this answer is grounded and useful.

Question:
{question}

Draft answer:
{draft}

Retrieved sources:
{retrieval.get("sources", [])}

Retrieved context:
{retrieval.get("context", "")}

Return:
- Grounded: Yes/Partial/No
- Missing evidence:
- Suggested correction:
"""


def _execute_tool(
    action: str,
    tool_input: str,
    question: str,
    retrieval: dict[str, Any],
    llm_call: Callable[[str], str],
) -> dict[str, Any]:
    if action == "retrieve":
        return {
            "tool": "retrieve",
            "input": tool_input or question,
            "result": {
                "retrieved_chunks": retrieval.get("retrieved_chunks", 0),
                "sources": retrieval.get("sources", []),
                "weak_retrieval": retrieval.get("weak_retrieval", False),
                "context_preview": retrieval.get("context", "")[:900],
            },
        }

    if action == "analyze":
        prompt = f"""
Analyze the evidence for this banking/compliance question.

Question:
{question}

Evidence:
{retrieval.get("context", "")}

Give concise findings only.
"""
        return {
            "tool": "analyze",
            "input": tool_input,
            "result": llm_call(prompt),
        }

    if action == "compare":
        prompt = f"""
Compare the available evidence and identify the strongest answer path.

Question:
{question}

Sources:
{retrieval.get("sources", [])}

Context:
{retrieval.get("context", "")}

Return concise comparison.
"""
        return {
            "tool": "compare",
            "input": tool_input,
            "result": llm_call(prompt),
        }

    if action == "self_check":
        draft_prompt = _final_answer_prompt(question, [], [], retrieval)
        draft = llm_call(draft_prompt)
        check = llm_call(_self_check_prompt(question, draft, retrieval))
        return {
            "tool": "self_check",
            "input": tool_input,
            "result": check,
        }

    return {
        "tool": "finish",
        "input": tool_input,
        "result": "Agent decided enough information is available.",
    }


def run_autonomous_agent(
    question: str,
    retrieval: dict[str, Any],
    llm_call: Callable[[str], str],
    memory: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    start = time.perf_counter()
    memory = memory or []

    agent_steps: list[dict[str, Any]] = []
    observations: list[dict[str, Any]] = []

    for step_index in range(MAX_AGENT_STEPS):
        planner_prompt = _agent_planner_prompt(question, memory, observations)
        planner_output = llm_call(planner_prompt)
        decision = _safe_json_loads(planner_output)

        action = str(decision.get("action", "finish")).strip().lower()
        thought = str(decision.get("thought", "")).strip()
        tool_input = str(decision.get("input", "")).strip()

        step = {
            "step": step_index + 1,
            "thought": thought,
            "action": action,
            "input": tool_input,
        }
        agent_steps.append(step)

        if action == "finish":
            break

        observation = _execute_tool(
            action=action,
            tool_input=tool_input,
            question=question,
            retrieval=retrieval,
            llm_call=llm_call,
        )
        observations.append(observation)

        if action == "self_check":
            break

    final_prompt = _final_answer_prompt(
        question=question,
        agent_steps=agent_steps,
        observations=observations,
        retrieval=retrieval,
    )
    answer = llm_call(final_prompt)

    latency_ms = round((time.perf_counter() - start) * 1000)

    confidence = "High"
    if retrieval.get("weak_retrieval"):
        confidence = "Medium"
    if not retrieval.get("sources"):
        confidence = "Low"

    return {
        "answer": answer,
        "backend": "Autonomous Agentic AI",
        "model_name": "autonomous-agentic-rag",
        "latency_ms": latency_ms,
        "confidence": confidence,
        "available": True,
        "agent_steps": agent_steps,
        "agent_observations": observations,
        "route_reason": "autonomous_agent_loop",
        "selection_reason": "Used multi-step planning, tool execution, evidence analysis, and self-check before final answer.",
    }
