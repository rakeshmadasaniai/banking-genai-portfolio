from __future__ import annotations

import json
import os
import re
import time
import traceback
from typing import Any, Callable

from openai import OpenAI


MAX_AGENT_STEPS = 8
DEFAULT_MODEL = os.getenv("OPENAI_AGENT_MODEL", "gpt-4o-mini")

SYSTEM_PROMPT = """
You are an Agentic Banking & Finance AI Workspace.

You are not a normal chatbot.
You must solve user requests by deciding when to use tools.

Available capabilities:
- Retrieve banking/compliance evidence
- Analyze uploaded document text
- Classify compliance domain
- Compare regulations or policies
- Calculate simple financial/compliance numbers
- Verify whether final answer is grounded in evidence
- Generate final report

Rules:
1. Use tools whenever evidence, calculation, comparison, or document analysis is needed.
2. Do not invent legal, compliance, investment, or financial advice.
3. Always ground banking/compliance answers in retrieved evidence when possible.
4. If evidence is weak, call retrieval again with a better query.
5. Do not expose hidden chain-of-thought.
6. Show only concise action summaries in the trace.
7. Final answer must include a short disclaimer.
8. If user asks for investment recommendations, provide educational scenarios (not personalized financial advice).
"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "retrieval_tool",
            "description": "Retrieve relevant banking and compliance evidence from app knowledge.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "top_k": {"type": "integer", "default": 5},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "portfolio_scenario_tool",
            "description": "Create educational diversified portfolio scenarios and calculate projected returns.",
            "parameters": {
                "type": "object",
                "properties": {
                    "amount": {"type": "number"},
                    "years": {"type": "integer"},
                    "risk_profile": {"type": "string"},
                    "expected_return": {"type": "number"},
                },
                "required": ["amount", "years", "risk_profile", "expected_return"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "document_analysis_tool",
            "description": "Analyze uploaded document text and extract relevant clauses, risks, obligations, or summary.",
            "parameters": {
                "type": "object",
                "properties": {"task": {"type": "string"}},
                "required": ["task"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compliance_classifier_tool",
            "description": "Classify the compliance category for a user query or evidence.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}, "context": {"type": "string"}},
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "finance_calculator_tool",
            "description": "Perform simple numeric calculations and threshold checks.",
            "parameters": {
                "type": "object",
                "properties": {"expression_or_text": {"type": "string"}},
                "required": ["expression_or_text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "comparison_tool",
            "description": "Compare two or more banking, finance, or regulatory concepts using available context.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}, "context": {"type": "string"}},
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "verification_tool",
            "description": "Verify whether a draft answer is supported by evidence and return groundedness status.",
            "parameters": {
                "type": "object",
                "properties": {"answer": {"type": "string"}, "evidence": {"type": "string"}},
                "required": ["answer", "evidence"],
            },
        },
    },
]


class AgenticRuntime:
    def __init__(self, retriever: Callable[[str, int], dict[str, Any]] | None = None) -> None:
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not api_key:
            raise ValueError("OPENAI_API_KEY is missing.")
        self.client = OpenAI(api_key=api_key)
        self.retriever = retriever

    def retrieval_tool(self, query: str, top_k: int = 5) -> dict[str, Any]:
        try:
            if self.retriever is None:
                return {"status": "error", "message": "Retriever is not connected.", "evidence": []}
            result = self.retriever(query, top_k)
            cards = result.get("source_cards", []) if isinstance(result, dict) else []
            evidence = [
                {
                    "source": c.get("label", "Unknown"),
                    "text": c.get("preview", ""),
                    "score": c.get("score"),
                }
                for c in cards[:top_k]
            ]
            return {
                "status": "success",
                "query": query,
                "evidence_count": len(evidence),
                "sources": result.get("sources", []) if isinstance(result, dict) else [],
                "context": result.get("context", "") if isinstance(result, dict) else "",
                "weak_retrieval": bool(result.get("weak_retrieval", False)) if isinstance(result, dict) else False,
                "evidence": evidence,
            }
        except Exception as exc:
            return {"status": "error", "message": str(exc), "traceback": traceback.format_exc(), "evidence": []}

    def document_analysis_tool(self, task: str, uploaded_text: str = "") -> dict[str, Any]:
        if not uploaded_text.strip():
            return {"status": "no_document", "message": "No uploaded document text was provided."}
        return {
            "status": "success",
            "task": task,
            "document_excerpt": uploaded_text[:8000],
            "summary": "Uploaded document text is available for reasoning.",
        }

    def compliance_classifier_tool(self, query: str, context: str = "") -> dict[str, Any]:
        text = f"{query}\n{context}".lower()
        keyword_map = {
            "KYC": ["kyc", "know your customer", "customer identification", "cip"],
            "AML": ["aml", "money laundering", "sar", "suspicious activity", "ctr"],
            "FDIC": ["fdic", "deposit insurance", "insured deposit"],
            "RBI": ["rbi", "reserve bank of india", "india"],
            "Basel III": ["basel", "capital adequacy", "tier 1", "risk-weighted"],
            "Fraud/Risk": ["fraud", "risk", "control", "monitoring"],
            "General Finance": ["loan", "bank", "interest", "credit", "deposit"],
        }
        categories = [k for k, keys in keyword_map.items() if any(t in text for t in keys)]
        return {
            "status": "success",
            "categories": categories or ["General Banking/Finance"],
            "reason": "Classified using domain keyword signals.",
        }

    def finance_calculator_tool(self, expression_or_text: str) -> dict[str, Any]:
        text = expression_or_text.strip()
        if not re.fullmatch(r"[0-9\.\+\-\*\/\(\)\s,%]+", text):
            return {
                "status": "needs_manual_reasoning",
                "message": "Input is not a clean numeric expression; reason from text.",
                "input": text,
            }
        try:
            result = eval(text.replace("%", "/100"), {"__builtins__": {}}, {})
            return {"status": "success", "input": expression_or_text, "result": result}
        except Exception as exc:
            return {"status": "error", "message": str(exc), "input": expression_or_text}

    def comparison_tool(self, query: str, context: str = "") -> dict[str, Any]:
        return {
            "status": "success",
            "query": query,
            "context": context[:6000],
            "instruction": "Use provided context and evidence to produce a structured comparison.",
        }

    def portfolio_scenario_tool(
        self,
        amount: float,
        years: int,
        risk_profile: str,
        expected_return: float,
    ) -> dict[str, Any]:
        try:
            principal = float(amount)
            horizon = int(years)
            exp_ret = float(expected_return)
            future_value = principal * ((1 + exp_ret) ** horizon)
            gain = future_value - principal
            return {
                "status": "success",
                "amount": principal,
                "years": horizon,
                "risk_profile": risk_profile,
                "expected_return": exp_ret,
                "future_value": round(future_value, 2),
                "estimated_gain": round(gain, 2),
                "disclaimer": "Educational scenario only, not financial advice.",
            }
        except Exception as exc:
            return {"status": "error", "message": str(exc)}

    def verification_tool(self, answer: str, evidence: str) -> dict[str, Any]:
        answer_terms = set(answer.lower().split())
        evidence_terms = set(evidence.lower().split())
        overlap = len(answer_terms.intersection(evidence_terms))
        score = min(overlap / max(len(answer_terms), 1), 1.0)
        status = "strong" if score >= 0.35 else ("medium" if score >= 0.18 else "weak")
        return {
            "status": "success",
            "groundedness": status,
            "score": round(score, 3),
            "recommendation": "Proceed" if status != "weak" else "Retrieve more evidence before final answer.",
        }

    def execute_tool(self, tool_name: str, args: dict[str, Any], uploaded_text: str = "") -> dict[str, Any]:
        if tool_name == "retrieval_tool":
            return self.retrieval_tool(args.get("query", ""), int(args.get("top_k", 5)))
        if tool_name == "document_analysis_tool":
            return self.document_analysis_tool(args.get("task", ""), uploaded_text=uploaded_text)
        if tool_name == "compliance_classifier_tool":
            return self.compliance_classifier_tool(args.get("query", ""), context=args.get("context", ""))
        if tool_name == "finance_calculator_tool":
            return self.finance_calculator_tool(args.get("expression_or_text", ""))
        if tool_name == "comparison_tool":
            return self.comparison_tool(args.get("query", ""), context=args.get("context", ""))
        if tool_name == "portfolio_scenario_tool":
            return self.portfolio_scenario_tool(
                amount=args.get("amount", 0),
                years=args.get("years", 10),
                risk_profile=args.get("risk_profile", "moderate"),
                expected_return=args.get("expected_return", 0.06),
            )
        if tool_name == "verification_tool":
            return self.verification_tool(args.get("answer", ""), args.get("evidence", ""))
        return {"status": "error", "message": f"Unknown tool: {tool_name}"}

    def run_agentic_workflow(
        self,
        user_query: str,
        uploaded_text: str = "",
        chat_history: list[dict[str, str]] | None = None,
        model: str = DEFAULT_MODEL,
    ) -> dict[str, Any]:
        started = time.time()
        trace: list[dict[str, Any]] = []
        messages: list[dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT}]

        if chat_history:
            for msg in chat_history[-8:]:
                if msg.get("role") in {"user", "assistant"}:
                    content = msg.get("content") or msg.get("answer") or ""
                    messages.append({"role": msg["role"], "content": content})
        if uploaded_text:
            messages.append(
                {
                    "role": "system",
                    "content": "Uploaded text is available through document_analysis_tool. Use it when needed.",
                }
            )

        messages.append({"role": "user", "content": user_query})
        final_answer = None
        last_retrieval: dict[str, Any] = {}

        for step in range(1, MAX_AGENT_STEPS + 1):
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
                temperature=0.2,
            )
            assistant_message = response.choices[0].message

            if assistant_message.tool_calls:
                messages.append(assistant_message.model_dump(exclude_none=True))
                for tool_call in assistant_message.tool_calls:
                    tool_name = tool_call.function.name
                    try:
                        args = json.loads(tool_call.function.arguments or "{}")
                    except Exception:
                        args = {}
                    result = self.execute_tool(tool_name, args, uploaded_text=uploaded_text)
                    if tool_name == "retrieval_tool":
                        last_retrieval = result
                    trace.append(
                        {
                            "step": step,
                            "tool": tool_name,
                            "args": args,
                            "observation": json.dumps(result, ensure_ascii=False)[:1200],
                        }
                    )
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": json.dumps(result, ensure_ascii=False),
                        }
                    )
            else:
                final_answer = assistant_message.content
                break

        if not final_answer:
            final_answer = "I reached the maximum agent steps before producing a final answer. Please narrow the question and try again."

        latency_ms = round((time.time() - started) * 1000)
        grounded = "High"
        if last_retrieval.get("weak_retrieval"):
            grounded = "Moderate"
        if not last_retrieval.get("sources"):
            grounded = "Low"

        return {
            "answer": final_answer,
            "trace": trace,
            "latency_ms": latency_ms,
            "steps": len(trace),
            "backend": "Agentic Workspace",
            "model_name": model,
            "confidence": grounded,
            "available": True,
            "agent_steps": trace,
            "agent_observations": [t.get("observation", "") for t in trace],
            "route_reason": "agentic_tool_calling",
            "selection_reason": "Model autonomously selected tools and iterated until final answer.",
        }
