"""
core/agentic_runtime.py
=======================
Agentic Workspace — Banking & Finance AI
(mode name: "Agentic Workspace" — use this string everywhere in UI)

TRUE agentic behavior:
  - LLM picks tools via OpenAI function-calling (tools=[])
  - Real while-loop: Think → Act → Observe → repeat until done
  - Tool results fed back to LLM so it decides the next step
  - Self-correction: detects weak answers and retries retrieval
  - Investor-specific regulations (not generic bank rules)
  - Age/context-aware risk profile inference
  - Verification enforced before final answer (LLM judge on High confidence)
  - Full agent trace for UI rendering
  - Retriever passed in → uses real FAISS/BM25 banking knowledge base
  - Document tool supports PDF/DOCX via pypdf2 + python-docx with graceful fallback
"""
from __future__ import annotations

import json
import math
import os
import re
import time
from typing import Any
try:
    import streamlit as st
except Exception:
    st = None

# ── Optional imports (graceful fallback if not installed) ──────────────────────
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# ─────────────────────────────────────────────────────────────────────────────
# SYSTEM PROMPT
# ─────────────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """
You are a production-grade Agentic Banking & Finance AI Workspace.

You must use tools for multi-step finance, compliance, investment, portfolio,
calculation, document, and regulatory tasks.

Rules:
1. Do not answer complex multi-step questions directly.
2. Use tools when calculations, portfolio construction, retrieved evidence,
   market context, or compliance checks are needed.
3. Never assume missing risk profile details.
4. If risk profile, goal, horizon, or liquidity needs are missing, ask a
   clarification question and stop.
5. For investment questions, provide educational scenarios only, not personalized
   financial advice.
6. Use market_data_tool only as supporting market context, not as a guarantee
   of future returns.
7. Always verify the final answer.
8. If verification fails, rewrite using only retrieved evidence and tool results.
9. Never expose hidden chain-of-thought. Show concise action summaries only.
10. CRITICAL: If time horizon is <= 12 months, treat liquidity as high and
    prioritize capital preservation. Do not ask redundant risk clarification
    and do not recommend equities, REITs, or long-duration products.
11. CRITICAL: For any regulatory/compliance/jurisdiction question, you MUST
    call retrieve_banking_context before answering. If retrieval is not used,
    the answer is invalid and must be retried with retrieval.
12. For comparison questions, return a structured Markdown table with columns:
    Requirement | Jurisdiction A | Jurisdiction B | Jurisdiction C | Notes.
13. ACTION RULES:
    - Never ask for information already present.
    - Never ask more than one clarification question in a response.
    - Never say "you should compare" when tools can compare now.
    - Act on available data first; ask only when a critical variable is missing.
14. MATH RULE:
    For questions like "what return do I need", "can I retire", "how long to reach X":
    call return_projection_tool first and compute required return scenarios.
    If required annual return > 15%, label it unrealistic and suggest alternatives.
""".strip()

# ─────────────────────────────────────────────────────────────────────────────
# TOOL DEFINITIONS  (passed to OpenAI tools=[])
# ─────────────────────────────────────────────────────────────────────────────

TOOLS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "retrieve_banking_context",
            "description": (
                "Search the banking/finance knowledge base for regulatory, compliance, "
                "or financial information. Use for any specific facts, definitions, or rules."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Specific search query."},
                    "focus": {
                        "type": "string",
                        "enum": ["regulation", "compliance", "risk", "capital", "investor", "general"],
                        "description": "Thematic focus of the search.",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "risk_profile_tool",
            "description": (
                "Analyze the user query and chat history to determine whether enough "
                "information exists to infer a risk profile. Returns signals found, "
                "whether profile can be inferred, and clarification questions if missing."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "user_query": {"type": "string"},
                    "chat_history_summary": {
                        "type": "string",
                        "description": "Summary or last few turns of chat history.",
                    },
                },
                "required": ["user_query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "portfolio_builder_tool",
            "description": (
                "Build an educational diversified portfolio allocation based on risk profile, "
                "investment amount, and time horizon. Returns full asset-class breakdown."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "amount": {"type": "number", "description": "Total investment in USD."},
                    "risk_profile": {
                        "type": "string",
                        "enum": ["conservative", "moderate", "aggressive"],
                    },
                    "horizon_years": {"type": "integer", "description": "Investment horizon in years."},
                },
                "required": ["amount", "risk_profile", "horizon_years"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "return_projection_tool",
            "description": (
                "Calculate compound future value and estimated gain using a weighted return rate."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "amount": {"type": "number"},
                    "horizon_years": {"type": "integer"},
                    "weighted_return": {
                        "type": "number",
                        "description": "Blended annual return as a decimal (e.g., 0.072 for 7.2%).",
                    },
                },
                "required": ["amount", "horizon_years", "weighted_return"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "investor_regulation_tool",
            "description": (
                "Return investor-specific regulatory rules relevant to an individual investor. "
                "NOT generic bank regulations. Covers FDIC limits, accredited investor rules, "
                "tax implications, and suitability requirements."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "amount": {"type": "number", "description": "Investment amount in USD."},
                    "investor_type": {
                        "type": "string",
                        "enum": ["individual", "joint", "trust", "corporate"],
                        "default": "individual",
                    },
                    "risk_profile": {"type": "string"},
                },
                "required": ["amount"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compliance_classifier_tool",
            "description": (
                "Classify and summarize a compliance or regulatory query. "
                "Identifies applicable frameworks (AML, KYC, Basel III, FDIC, Dodd-Frank, etc.)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "context": {
                        "type": "string",
                        "description": "Retrieved regulatory context to classify against.",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compliance_checker_tool",
            "description": (
                "Check ratio-based compliance against frameworks such as Basel III and "
                "return PASS/FAIL by metric."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "ratios": {
                        "type": "object",
                        "description": "Map of ratio name to numeric value, e.g. cet1, tier1, total_capital, leverage.",
                    },
                    "framework": {
                        "type": "string",
                        "description": "Compliance framework name.",
                        "default": "basel_iii",
                    },
                },
                "required": ["ratios"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "document_analysis_tool",
            "description": (
                "Analyze uploaded documents (PDF, DOCX, TXT, CSV) and extract key clauses, "
                "summaries, compliance issues, or financial figures."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "analysis_type": {
                        "type": "string",
                        "enum": ["summary", "key_clauses", "compliance_check", "financial_figures", "comparison"],
                    },
                    "query": {"type": "string", "description": "What to look for in the documents."},
                },
                "required": ["analysis_type", "query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "verification_tool",
            "description": (
                "Verify whether the draft answer is grounded in retrieved evidence. "
                "Returns a confidence score and whether a retry is needed."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "draft_answer": {"type": "string"},
                    "evidence_summary": {
                        "type": "string",
                        "description": "Summary of the evidence retrieved so far.",
                    },
                },
                "required": ["draft_answer", "evidence_summary"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "market_data_tool",
            "description": "Fetch recent benchmark market data for ETFs, indexes, or funds such as SPY, BND, VXUS, QQQ, or VTI.",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbols": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Ticker symbols to fetch market data for.",
                    }
                },
                "required": ["symbols"],
            },
        },
    },
]

# ─────────────────────────────────────────────────────────────────────────────
# PORTFOLIO DATA
# ─────────────────────────────────────────────────────────────────────────────

_PORTFOLIOS = {
    "conservative": {
        "US Bonds / Treasuries":               (0.45, 0.040),
        "High-Yield Savings / Money Market":   (0.20, 0.035),
        "Dividend Equities":                   (0.20, 0.070),
        "REITs":                               (0.10, 0.070),
        "International Equities":              (0.05, 0.075),
    },
    "moderate": {
        "US Broad Market Equities":            (0.40, 0.085),
        "US Bonds / Treasuries":               (0.25, 0.040),
        "International Equities":              (0.15, 0.075),
        "REITs":                               (0.10, 0.070),
        "High-Yield Savings / Money Market":   (0.10, 0.035),
    },
    "aggressive": {
        "US Broad Market Equities":            (0.55, 0.085),
        "International Equities":              (0.20, 0.075),
        "Growth / Technology Equities":        (0.10, 0.100),
        "REITs":                               (0.10, 0.070),
        "Cash / Money Market":                 (0.05, 0.030),
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# AGENTIC RUNTIME CLASS
# ─────────────────────────────────────────────────────────────────────────────

class AgenticRuntime:
    """
    True autonomous agent using OpenAI tool-calling with a real while-loop.
    The LLM decides which tool to call and when to stop — Python never
    hard-codes the execution order.
    """

    MAX_STEPS = 8

    def __init__(self, retriever=None, uploaded_docs=None):
        self.retriever = retriever          # your existing retriever object
        self.uploaded_docs = uploaded_docs or []
        self.api_key = os.environ.get("OPENAI_API_KEY", "").strip()
        self.model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini").strip()
        self._evidence_buffer: list[str] = []

    # ── Public entry point ────────────────────────────────────────────────────

    def run(
        self,
        user_query: str,
        chat_history: list[dict] | None = None,
    ) -> dict:
        """
        Run the full agentic loop.

        Returns
        -------
        {
          "answer": str,
          "trace": list[dict],       # for the UI trace panel
          "tools_used": list[str],
          "confidence": str,
          "latency_ms": int,
          "requires_clarification": bool,
          "clarification_questions": list[str],
        }
        """
        start = time.perf_counter()
        trace: list[dict] = []
        tools_used: list[str] = []
        self._evidence_buffer = []

        if not OPENAI_AVAILABLE or not self.api_key:
            return self._fallback(user_query, "OpenAI API key not configured.")

        client = OpenAI(api_key=self.api_key)

        # Build initial message list
        history_summary = self._summarise_history(chat_history or [])
        profile_block = ""
        if st is not None:
            profile_block = (
                "Known user investment profile:\n"
                f"Risk profile: {st.session_state.get('risk_profile')}\n"
                f"Investment goal: {st.session_state.get('investment_goal')}\n"
                f"Liquidity need: {st.session_state.get('liquidity_need')}\n"
                f"Investment horizon: {st.session_state.get('investment_horizon')}"
            )
        messages: list[dict] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "system", "content": profile_block} if profile_block else {"role": "system", "content": "No prior investment profile stored."},
            {
                "role": "user",
                "content": (
                    f"{user_query}\n\n"
                    f"[Chat history summary: {history_summary}]"
                    if history_summary
                    else user_query
                ),
            },
        ]

        requires_retrieval = self._requires_regulatory_retrieval(user_query)
        comparison_request = self._is_comparison_question(user_query)
        math_first_request = self._is_math_planning_question(user_query)
        if requires_retrieval:
            messages.append(
                {
                    "role": "system",
                    "content": (
                        "Mandatory policy: call retrieve_banking_context before final answer "
                        "for this query."
                    ),
                }
            )
        if comparison_request:
            messages.append(
                {
                    "role": "system",
                    "content": (
                        "Output policy: format comparison answers as a markdown table with columns "
                        "Requirement | Jurisdiction A | Jurisdiction B | Jurisdiction C | Notes."
                    ),
                }
            )
        if math_first_request:
            messages.append(
                {
                    "role": "system",
                    "content": (
                        "Math-first policy: use return_projection_tool before asking for additional profile data. "
                        "If required annual return exceeds 15%, mark as unrealistic and suggest alternatives."
                    ),
                }
            )

        trace.append({"step": "start", "label": "🧠 Intent analysis", "detail": user_query})

        # ── Safety preflight for investment planning ──────────────────────────
        # This prevents the agent from fabricating a risk profile or producing
        # a personalized portfolio when required user details are missing.
        if self._looks_like_investment_request(user_query):
            risk_result = self._risk_profile_tool(
                user_query=user_query,
                chat_history_summary=history_summary,
            )
            tools_used.append("risk_profile_tool")
            trace.append({
                "step": "tool_call",
                "label": "🔧 risk_profile_tool",
                "detail": json.dumps({
                    "user_query": user_query,
                    "chat_history_summary": history_summary,
                    "preflight": True,
                }, indent=2),
            })
            trace.append({
                "step": "observation",
                "label": "📋 Result: risk_profile_tool",
                "detail": json.dumps(risk_result)[:600],
            })

            if not risk_result.get("enough_information", False):
                latency_ms = round((time.perf_counter() - start) * 1000)
                questions = risk_result.get("required_clarification", [])
                return {
                    "answer": (
                        "I need a little more information before I can build an educational investment scenario.\n\n"
                        "Please clarify:\n"
                        + "\n".join(f"{i+1}. {q}" for i, q in enumerate(questions))
                        + "\n\n⚠️ Educational scenario only. Not personalized financial, legal, or investment advice."
                    ),
                    "trace": trace + [{
                        "step": "complete",
                        "label": "✅ Agent paused for clarification",
                        "detail": "Risk profile, goal, or liquidity needs are missing.",
                    }],
                    "tools_used": tools_used,
                    "confidence": "High",
                    "latency_ms": latency_ms,
                    "requires_clarification": True,
                    "clarification_questions": questions,
                    "evidence_count": len(self._evidence_buffer),
                }

            # Feed validated risk profile into the LLM context so it can continue
            # with portfolio_builder_tool, return_projection_tool, regulation, and verification.
            messages.append({
                "role": "system",
                "content": "Risk profile preflight result: " + json.dumps(risk_result),
            })

        # ── TRUE AGENTIC WHILE-LOOP ───────────────────────────────────────────
        steps = 0
        final_answer = ""
        requires_clarification = False
        clarification_questions: list[str] = []
        self_correction_attempts = 0
        max_self_corrections = 1

        while steps < self.MAX_STEPS:
            steps += 1

            try:
                response = client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=TOOLS,
                    tool_choice="auto",
                    temperature=0.0,
                    max_tokens=1200,
                )
            except Exception as exc:
                return self._fallback(user_query, f"OpenAI error: {exc}")

            choice = response.choices[0]

            # ── LLM decided it is done ─────────────────────────────────────
            if choice.finish_reason == "stop":
                final_answer = (choice.message.content or "").strip()
                if requires_retrieval and "retrieve_banking_context" not in tools_used:
                    messages.append(
                        {
                            "role": "user",
                            "content": (
                                "Invalid attempt: you did not call retrieve_banking_context for this "
                                "regulatory/compliance query. Call retrieve_banking_context now and rewrite."
                            ),
                        }
                    )
                    trace.append(
                        {
                            "step": steps,
                            "tool": "retrieval_enforcer",
                            "observation": "Final answer rejected because retrieval tool was not used.",
                        }
                    )
                    final_answer = None
                    continue
                if final_answer and hasattr(self, "_evidence_buffer") and self._evidence_buffer:
                    verify_result = self._verification_tool(
                        draft_answer=final_answer,
                        evidence_summary=" ".join(self._evidence_buffer)
                    )

                    if bool(verify_result.get("needs_retry")) and self_correction_attempts < max_self_corrections:
                        self_correction_attempts += 1
                        messages.append({
                            "role": "assistant",
                            "content": final_answer
                        })

                        messages.append({
                            "role": "user",
                            "content": (
                                f"Your answer has issues:\n"
                                f"Recommendation: {verify_result.get('recommendation')}\n"
                                f"Unsupported claims: {verify_result.get('unsupported_claims', [])}\n\n"
                                "Rewrite the answer using only retrieved evidence and tool results. "
                                "Do not add new assumptions. "
                                "Do not assume missing user details. "
                                "If risk profile is missing, ask a clarification question instead of guessing."
                            )
                        })

                        trace.append({
                            "step": steps,
                            "tool": "self_correction_loop",
                            "observation": "Verification failed. Agent is rewriting the answer using existing evidence and tool results."
                        })

                        final_answer = None
                        continue

                trace.append({
                    "step": "complete",
                    "label": "? Agent complete",
                    "detail": f"Finished in {steps} steps",
                })
                break

            # ── LLM wants to call tools ────────────────────────────────────
            if choice.finish_reason == "tool_calls":
                tool_calls = choice.message.tool_calls or []

                # Append assistant message with tool_calls
                messages.append({
                    "role": "assistant",
                    "content": choice.message.content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            },
                        }
                        for tc in tool_calls
                    ],
                })

                for tc in tool_calls:
                    tool_name = tc.function.name
                    try:
                        args = json.loads(tc.function.arguments or "{}")
                    except json.JSONDecodeError:
                        args = {}

                    tools_used.append(tool_name)
                    trace.append({
                        "step": "tool_call",
                        "label": f"🔧 {tool_name}",
                        "detail": json.dumps(args, indent=2),
                    })

                    # Execute the tool
                    result = self._execute_tool(tool_name, args)

                    # Check for clarification requests from risk_profile_tool
                    if (
                        tool_name == "risk_profile_tool"
                        and isinstance(result, dict)
                        and not result.get("enough_information", True)
                    ):
                        requires_clarification = True
                        clarification_questions = result.get("required_clarification", [])

                    result_str = json.dumps(result)
                    self._evidence_buffer.append(f"{tool_name}: {result_str[:400]}")

                    trace.append({
                        "step": "observation",
                        "label": f"📋 Result: {tool_name}",
                        "detail": result_str[:600],
                    })

                    # Feed observation back to LLM
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": result_str,
                    })

                continue  # let LLM decide next step

            # Unexpected finish reason
            break

        latency_ms = round((time.perf_counter() - start) * 1000)

        # If clarification needed, override final answer
        if requires_clarification and clarification_questions:
            final_answer = (
                "I need a little more information before I can build your investment plan.\n\n"
                "Please clarify:\n"
                + "\n".join(f"{i+1}. {q}" for i, q in enumerate(clarification_questions))
            )

        # Ensure we never return a blank answer after tool execution.
        if not final_answer and self._evidence_buffer:
            final_answer = (
                "I gathered evidence but could not fully finalize a verified response in one pass. "
                "Here is the grounded summary from the executed tools:\n\n"
                + "\n".join(f"- {item[:220]}" for item in self._evidence_buffer[:6])
                + "\n\n⚠️ Educational guidance only. Not personalized financial, legal, or investment advice."
            )

        confidence = self._score_confidence(final_answer, tools_used)

        return {
            "answer": final_answer or "I was unable to generate a grounded answer. Please try rephrasing.",
            "trace": trace,
            "tools_used": list(dict.fromkeys(tools_used)),  # deduplicated, order-preserving
            "confidence": confidence,
            "latency_ms": latency_ms,
            "requires_clarification": requires_clarification,
            "clarification_questions": clarification_questions,
            "evidence_count": len(self._evidence_buffer),
        }

    # ── Tool dispatcher ───────────────────────────────────────────────────────

    def _execute_tool(self, tool_name: str, args: dict) -> Any:
        dispatch = {
            "retrieve_banking_context":  self._retrieve_banking_context,
            "risk_profile_tool":         self._risk_profile_tool,
            "portfolio_builder_tool":    self._portfolio_builder_tool,
            "return_projection_tool":    self._return_projection_tool,
            "market_data_tool":          self.market_data_tool,
            "investor_regulation_tool":  self._investor_regulation_tool,
            "compliance_classifier_tool": self._compliance_classifier_tool,
            "compliance_checker_tool":   self._compliance_checker_tool,
            "document_analysis_tool":    self._document_analysis_tool,
            "verification_tool":         self._verification_tool,
        }
        fn = dispatch.get(tool_name)
        if fn is None:
            return {"status": "error", "message": f"Unknown tool: {tool_name}"}
        try:
            return fn(**args)
        except Exception as exc:
            return {"status": "error", "message": str(exc)}

    # ─────────────────────────────────────────────────────────────────────────
    # TOOL IMPLEMENTATIONS
    # ─────────────────────────────────────────────────────────────────────────

    def _retrieve_banking_context(self, query: str, focus: str = "general") -> dict:
        """Use the existing retriever or fall back to knowledge-base hints."""
        if self.retriever is not None:
            # 1) Generic retriever object support: search(), retrieve(), or callable.
            try:
                if hasattr(self.retriever, "search"):
                    raw_results = self.retriever.search(query)
                elif hasattr(self.retriever, "retrieve"):
                    raw_results = self.retriever.retrieve(query)
                elif callable(self.retriever):
                    raw_results = self.retriever(query)
                else:
                    raw_results = None

                if raw_results:
                    if isinstance(raw_results, dict):
                        context = raw_results.get("context") or raw_results.get("text") or str(raw_results)
                        sources = raw_results.get("sources", [])
                        chunks = raw_results.get("retrieved_chunks", [])
                    else:
                        items = list(raw_results)[:5]
                        context_parts = []
                        sources = []
                        chunks = []
                        for item in items:
                            if isinstance(item, dict):
                                txt = item.get("text") or item.get("content") or item.get("page_content") or str(item)
                                src = item.get("source") or item.get("metadata", {}).get("source") or "Knowledge base"
                            else:
                                txt = getattr(item, "page_content", str(item))
                                src = getattr(item, "source", "Knowledge base")
                            context_parts.append(txt)
                            sources.append(src)
                            chunks.append(item)
                        context = "\n\n".join(context_parts)

                    return {
                        "status": "success",
                        "query": query,
                        "focus": focus,
                        "context": str(context)[:1200],
                        "sources": sources[:5],
                        "chunk_count": len(chunks) if chunks else len(sources),
                    }
            except Exception:
                pass

            # 2) Your app-specific proxy path: retrieve_shared_context(base_index, upload_index).
            try:
                from core.retriever import retrieve_shared_context
                base_index = getattr(self.retriever, "base_index", None)
                upload_index = getattr(self.retriever, "upload_index", None)
                result = retrieve_shared_context(query, base_index, upload_index)
                context = result.get("context", "")
                sources = result.get("sources", [])
                return {
                    "status": "success",
                    "query": query,
                    "focus": focus,
                    "context": context[:1200],
                    "sources": sources[:5],
                    "chunk_count": len(result.get("retrieved_chunks", [])),
                }
            except Exception:
                pass

        # Fallback: return structured knowledge hints
        hints = _KNOWLEDGE_HINTS.get(focus, _KNOWLEDGE_HINTS["general"])
        relevant = [h for h in hints if any(w in query.lower() for w in h["keywords"])]
        context = " ".join(h["text"] for h in relevant[:3]) if relevant else (
            "No specific context retrieved. Answer based on general banking knowledge."
        )
        return {
            "status": "fallback",
            "query": query,
            "focus": focus,
            "context": context,
            "sources": ["Banking knowledge base (local fallback)"],
            "chunk_count": len(relevant),
        }

    def _risk_profile_tool(
        self,
        user_query: str,
        chat_history_summary: str = "",
    ) -> dict:
        """
        Infer risk profile from query + history.
        Supports implicit signals (age, income language, loss aversion).
        """
        text = f"{user_query} {chat_history_summary}".lower()

        # Horizon detection (months + years)
        horizon_months = None
        month_match = re.search(r"(\d+)\s*(month|months)", text)
        year_match = re.search(r"(\d+)\s*(year|years)", text)
        if month_match:
            horizon_months = int(month_match.group(1))
        elif year_match:
            horizon_months = int(year_match.group(1)) * 12

        # Hard short-term override: no redundant clarification, force liquid conservative profile.
        if horizon_months is not None and horizon_months <= 12:
            return {
                "status": "success",
                "enough_information": True,
                "risk_profile": "conservative",
                "inferred_from": "time_horizon",
                "signals": {
                    "explicit_risk": None,
                    "age_inferred": None,
                    "loss_averse": True,
                    "growth_seeking": False,
                    "goal": "capital preservation",
                    "horizon_years": round(horizon_months / 12.0, 2),
                    "horizon_months": horizon_months,
                    "liquidity_need": "high",
                },
                "agent_instruction": (
                    f"User needs funds in {horizon_months} months. "
                    "Use only liquid, conservative options (HYSA, money market, T-bills, short-term CDs). "
                    "Do not use equities, REITs, or long-duration instruments."
                ),
                "required_clarification": [],
            }

        goal_map = {
            "retirement": ["retirement", "retire", "retiring", "retired", "pension"],
            "growth": ["growth", "grow", "appreciate"],
            "income": ["income", "dividend", "cash flow"],
            "preservation": ["preservation", "protect", "safe"],
        }
        detected_goal = None
        for g_name, g_keys in goal_map.items():
            if any(k in text for k in g_keys):
                detected_goal = g_name
                break

        # Explicit keyword signals
        explicit_risk = next(
            (r for r in ["conservative", "moderate", "aggressive"] if r in text),
            None,
        )

        # Age-based inference
        inferred_from_age = None
        age = None
        age_patterns = [
            r"i am (\d{2})\s*years?\s*old",
            r"i'm (\d{2})\s*years?\s*old",
            r"(\d{2})\s*years?\s*old",
            r"aged?\s*(\d{2})",
        ]
        age_match = None
        for p in age_patterns:
            age_match = re.search(p, text)
            if age_match:
                age = int(age_match.group(1))
                break
        if age_match:
            try:
                age = int(age or 0)
                if age >= 60:
                    inferred_from_age = "conservative"
                elif age >= 40:
                    inferred_from_age = "moderate"
                elif age >= 18:
                    inferred_from_age = "aggressive"
            except ValueError:
                pass

        # Loss-aversion language
        loss_averse = any(
            p in text
            for p in ["can't afford to lose", "cannot afford to lose", "don't want to lose",
                      "safe", "protect my", "no risk", "low risk"]
        )
        growth_seeking = any(
            p in text
            for p in ["maximize", "grow as much", "high return", "beat the market",
                      "aggressive growth", "10x", "high risk high reward"]
        )

        # Goal detection
        goal = detected_goal or next(
            (g for g in ["retirement", "growth", "income", "preservation", "education"] if g in text),
            None,
        )

        # Horizon detection
        horizon_match = re.search(r"(\d+)\s*year", text)
        horizon = int(horizon_match.group(1)) if horizon_match else None

        # Senior default assumptions: avoid blocking on generic "what should I do?"
        senior_default_assumption = False
        if inferred_from_age == "conservative":
            if not goal:
                goal = "retirement"
                senior_default_assumption = True
            if not horizon:
                horizon = 10
                senior_default_assumption = True

        # Determine profile. For investment planning, a profile alone is not enough;
        # the agent also needs a goal and a time/liquidity signal before building a portfolio.
        if explicit_risk:
            profile = explicit_risk
        elif loss_averse:
            profile = "conservative"
        elif growth_seeking:
            profile = "aggressive"
        elif inferred_from_age:
            profile = inferred_from_age
        else:
            profile = "unknown"

        enough = profile != "unknown" and bool(goal) and bool(horizon)

        clarifications = []
        if not explicit_risk and not loss_averse and not growth_seeking and not inferred_from_age:
            clarifications.append(
                "What is your risk tolerance? (conservative / moderate / aggressive)"
            )
        if not goal:
            clarifications.append(
                "What is your primary goal? (growth / income / preservation / retirement)"
            )
        if not horizon:
            clarifications.append(
                "Do you need access to this money within the next 1–3 years?"
            )

        return {
            "status": "success",
            "enough_information": enough,
            "risk_profile": profile,
            "inferred_from": (
                "explicit" if explicit_risk
                else "age" if inferred_from_age
                else "language" if (loss_averse or growth_seeking)
                else "insufficient"
            ),
            "signals": {
                "explicit_risk": explicit_risk,
                "age_inferred": inferred_from_age,
                "loss_averse": loss_averse,
                "growth_seeking": growth_seeking,
                "goal": goal,
                "horizon_years": horizon,
                "senior_default_assumption": senior_default_assumption,
            },
            "required_clarification": clarifications if not enough else [],
        }

    def _portfolio_builder_tool(
        self,
        amount: float,
        risk_profile: str,
        horizon_years: int = 10,
    ) -> dict:
        """Build a full asset-class allocation with weighted expected return."""
        if horizon_years <= 1:
            allocation = [
                {"asset_class": "High-Yield Savings Accounts", "allocation_pct": 35.0, "amount_usd": round(amount * 0.35, 2), "assumed_annual_return_pct": 4.8, "contribution_to_weighted_return": 1.68},
                {"asset_class": "Money Market Funds", "allocation_pct": 25.0, "amount_usd": round(amount * 0.25, 2), "assumed_annual_return_pct": 4.9, "contribution_to_weighted_return": 1.225},
                {"asset_class": "6-12 Month Treasury Bills", "allocation_pct": 25.0, "amount_usd": round(amount * 0.25, 2), "assumed_annual_return_pct": 5.0, "contribution_to_weighted_return": 1.25},
                {"asset_class": "Short-Term CDs", "allocation_pct": 15.0, "amount_usd": round(amount * 0.15, 2), "assumed_annual_return_pct": 4.7, "contribution_to_weighted_return": 0.705},
            ]
            weighted_return = 0.0486
            return {
                "status": "success",
                "risk_profile": "conservative",
                "investment_amount": amount,
                "horizon_years": horizon_years,
                "allocation": allocation,
                "weighted_expected_return": round(weighted_return, 4),
                "weighted_return_pct": round(weighted_return * 100, 2),
                "note": "Short-horizon safety override applied. Educational scenario only.",
            }

        profile_key = risk_profile.lower()
        allocation_data = _PORTFOLIOS.get(profile_key, _PORTFOLIOS["moderate"])

        rows = []
        weighted_return = 0.0
        for asset, (pct, ret) in allocation_data.items():
            dollars = amount * pct
            weighted_return += pct * ret
            rows.append({
                "asset_class": asset,
                "allocation_pct": round(pct * 100, 1),
                "amount_usd": round(dollars, 2),
                "assumed_annual_return_pct": round(ret * 100, 1),
                "contribution_to_weighted_return": round(pct * ret * 100, 3),
            })

        return {
            "status": "success",
            "risk_profile": profile_key,
            "investment_amount": amount,
            "horizon_years": horizon_years,
            "allocation": rows,
            "weighted_expected_return": round(weighted_return, 4),
            "weighted_return_pct": round(weighted_return * 100, 2),
            "note": "Educational scenario only. Not personalized financial advice.",
        }

    def _return_projection_tool(
        self,
        amount: float,
        horizon_years: int,
        weighted_return: float,
    ) -> dict:
        """Compound interest projection."""
        future_value = amount * math.pow(1 + weighted_return, horizon_years)
        gain = future_value - amount
        real_return = max(weighted_return - 0.03, 0.0)  # inflation-adjusted (assume 3% CPI)
        real_fv = amount * math.pow(1 + real_return, horizon_years)

        return {
            "status": "success",
            "principal_usd": round(amount, 2),
            "years": horizon_years,
            "weighted_annual_return_pct": round(weighted_return * 100, 2),
            "return_feasibility": "unrealistic" if weighted_return > 0.15 else "reasonable",
            "future_value_nominal_usd": round(future_value, 2),
            "estimated_gain_usd": round(gain, 2),
            "inflation_adjusted_future_value_usd": round(real_fv, 2),
            "assumed_inflation_rate_pct": 3.0,
            "note": "Projections are illustrative. Past performance does not guarantee future results.",
        }

    def _investor_regulation_tool(
        self,
        amount: float,
        investor_type: str = "individual",
        risk_profile: str = "moderate",
    ) -> dict:
        """
        Return INVESTOR-specific regulatory rules — not generic bank regulations.
        Covers FDIC limits, accredited investor thresholds, tax implications, suitability.
        """
        flags: list[dict] = []

        # FDIC limit check
        if amount > 250_000:
            excess = amount - 250_000
            flags.append({
                "rule": "FDIC Deposit Insurance Limit",
                "applies": True,
                "detail": (
                    f"Your ${amount:,.0f} exceeds the FDIC insured limit of $250,000 per "
                    f"depositor per bank. ${excess:,.0f} would be uninsured. "
                    "Consider spreading across multiple FDIC-member institutions or "
                    "using a brokerage sweep account."
                ),
                "severity": "high",
            })

        # Accredited investor threshold ($1M net worth, excl. primary residence)
        flags.append({
            "rule": "SEC Accredited Investor Status",
            "applies": amount >= 200_000,
            "detail": (
                "Investors with net worth > $1M (excluding primary residence) or income "
                "> $200K (individual) / $300K (joint) for 2+ years qualify as accredited. "
                "This unlocks private placements, hedge funds, and certain structured products."
            ),
            "severity": "informational",
        })

        # Tax implications
        tax_notes = [
            "Long-term capital gains (assets held >1 year): 0%, 15%, or 20% depending on income.",
            "Short-term capital gains taxed as ordinary income.",
            "REITs distribute ordinary income taxed at your marginal rate.",
            "Municipal bonds may offer tax-exempt interest at federal level.",
        ]
        if amount >= 100_000:
            tax_notes.append(
                "Consider a tax-loss harvesting strategy to offset gains with losses."
            )
        flags.append({
            "rule": "Federal Tax Implications",
            "applies": True,
            "detail": " ".join(tax_notes),
            "severity": "medium",
        })

        # Suitability / FINRA Rule 2111
        flags.append({
            "rule": "FINRA Suitability Rule 2111",
            "applies": True,
            "detail": (
                "Registered broker-dealers must ensure investment recommendations are "
                f"suitable for your {risk_profile} risk profile, financial situation, "
                "and investment objectives before executing trades."
            ),
            "severity": "informational",
        })

        # Retirement account contribution limits
        flags.append({
            "rule": "Retirement Account Limits (2024)",
            "applies": True,
            "detail": (
                "401(k) contribution limit: $23,000 ($30,500 if age 50+). "
                "IRA limit: $7,000 ($8,000 if age 50+). "
                "Consider maximizing tax-advantaged accounts before taxable accounts."
            ),
            "severity": "informational",
        })

        # Wash sale rule
        flags.append({
            "rule": "IRS Wash Sale Rule",
            "applies": True,
            "detail": (
                "You cannot claim a tax loss if you buy a substantially identical security "
                "within 30 days before or after a sale. Relevant for tax-loss harvesting strategies."
            ),
            "severity": "low",
        })

        high_severity = [f for f in flags if f["severity"] == "high"]

        return {
            "status": "success",
            "investor_type": investor_type,
            "investment_amount": amount,
            "regulatory_flags": flags,
            "high_severity_count": len(high_severity),
            "primary_warning": high_severity[0]["detail"] if high_severity else None,
            "note": "These are general educational notes. Consult a licensed financial advisor.",
        }

    def market_data_tool(self, symbols: list[str]) -> dict:
        try:
            import yfinance as yf

            results: dict[str, dict[str, Any]] = {}
            for symbol in symbols:
                ticker = yf.Ticker(symbol)
                info = ticker.history(period="1y")

                if info.empty:
                    results[symbol] = {"status": "no_data"}
                    continue

                start_price = float(info["Close"].iloc[0])
                end_price = float(info["Close"].iloc[-1])
                one_year_return = (end_price - start_price) / start_price
                results[symbol] = {
                    "status": "success",
                    "start_price": round(start_price, 2),
                    "end_price": round(end_price, 2),
                    "one_year_return_pct": round(one_year_return * 100, 2),
                }

            return {
                "status": "success",
                "data": results,
                "note": "Market data is recent historical data and does not predict future returns.",
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "note": "Market data unavailable. Use long-term assumptions as fallback.",
            }

    def _compliance_classifier_tool(self, query: str, context: str = "") -> dict:
        """Classify which compliance frameworks apply to a query."""
        query_lower = query.lower()
        context_lower = context.lower()
        combined = f"{query_lower} {context_lower}"

        frameworks = {
            "AML (Anti-Money Laundering)": ["aml", "money laundering", "suspicious activity", "sar", "bsa"],
            "KYC (Know Your Customer)":    ["kyc", "know your customer", "customer due diligence", "cdd", "identity verification"],
            "Basel III / Capital":         ["basel", "capital ratio", "tier 1", "lcr", "nsfr", "leverage ratio"],
            "FDIC":                        ["fdic", "deposit insurance", "insured deposit", "bank failure"],
            "Dodd-Frank":                  ["dodd-frank", "volcker", "proprietary trading", "systemically important"],
            "FINRA / SEC":                 ["finra", "sec", "broker-dealer", "suitability", "accredited investor"],
            "CFPB":                        ["cfpb", "consumer financial", "fair lending", "ecoa", "hmda"],
            "FATF":                        ["fatf", "financial action task force", "correspondent banking"],
        }

        matched = {
            fw: kws
            for fw, kws in frameworks.items()
            if any(k in combined for k in kws)
        }

        return {
            "status": "success",
            "query": query,
            "applicable_frameworks": list(matched.keys()),
            "framework_count": len(matched),
            "primary_framework": list(matched.keys())[0] if matched else "General Banking",
            "context_used": bool(context),
        }

    def _compliance_checker_tool(self, ratios: dict, framework: str = "basel_iii") -> dict:
        """Check ratio metrics against framework thresholds (PASS/FAIL)."""
        thresholds = {
            "basel_iii": {
                "cet1": 4.5,
                "tier1": 6.0,
                "total_capital": 8.0,
                "leverage": 3.0,
            }
        }
        limits = thresholds.get(framework.lower(), thresholds["basel_iii"])
        results = {}
        for k, v in (ratios or {}).items():
            key = str(k).lower().strip()
            if key in limits:
                try:
                    actual = float(v)
                except Exception:
                    continue
                required = limits[key]
                results[key] = {
                    "actual": actual,
                    "required": required,
                    "status": "PASS" if actual >= required else "FAIL",
                }
        overall = all(r["status"] == "PASS" for r in results.values()) if results else False
        return {
            "status": "success",
            "framework": framework,
            "results": results,
            "overall": overall,
            "note": "Regulatory thresholds are simplified reference values.",
        }

    def _document_analysis_tool(
        self,
        analysis_type: str,
        query: str,
    ) -> dict:
        """
        Analyse uploaded documents.
        Supports: PDF (via pypdf / PyPDF2), DOCX (via python-docx), TXT/CSV (raw).
        Graceful fallback if libraries are missing.
        """
        if not self.uploaded_docs:
            return {
                "status": "no_documents",
                "message": "No documents uploaded. Please upload a PDF, DOCX, or TXT file.",
                "analysis_type": analysis_type,
            }

        combined_text = ""
        doc_names = []

        for doc in self.uploaded_docs[:3]:
            name = getattr(doc, "name", "document")
            doc_names.append(name)
            ext = name.rsplit(".", 1)[-1].lower() if "." in name else "txt"

            try:
                # ── PDF extraction ────────────────────────────────────────────
                if ext == "pdf":
                    text = self._extract_pdf(doc)
                # ── DOCX extraction ───────────────────────────────────────────
                elif ext in ("docx", "doc"):
                    text = self._extract_docx(doc)
                # ── Plain text / CSV ──────────────────────────────────────────
                else:
                    raw = doc.read()
                    if isinstance(raw, bytes):
                        raw = raw.decode("utf-8", errors="ignore")
                    text = raw
                combined_text += f"\n\n=== {name} ===\n{text[:4000]}"
            except Exception as exc:
                combined_text += f"\n\n=== {name}: extraction failed ({exc}) ==="

        return {
            "status": "success" if combined_text.strip() else "empty",
            "documents_analysed": doc_names,
            "analysis_type": analysis_type,
            "query": query,
            "extracted_text_preview": combined_text[:2000],
            "char_count": len(combined_text),
            "note": "LLM will analyse the extracted text above to answer your query.",
        }

    @staticmethod
    def _extract_pdf(doc) -> str:
        """Extract text from a PDF file object. Tries pypdf then PyPDF2."""
        doc.seek(0)
        raw_bytes = doc.read()

        # Try pypdf (newer)
        try:
            import io
            import pypdf  # type: ignore
            reader = pypdf.PdfReader(io.BytesIO(raw_bytes))
            pages = [page.extract_text() or "" for page in reader.pages[:20]]
            return "\n".join(pages)
        except ImportError:
            pass

        # Try PyPDF2 (older)
        try:
            import io
            import PyPDF2  # type: ignore
            reader = PyPDF2.PdfReader(io.BytesIO(raw_bytes))
            pages = [page.extract_text() or "" for page in reader.pages[:20]]
            return "\n".join(pages)
        except ImportError:
            pass

        # Last resort: decode bytes
        return raw_bytes.decode("utf-8", errors="ignore")

    @staticmethod
    def _extract_docx(doc) -> str:
        """Extract text from a DOCX file object using python-docx."""
        doc.seek(0)
        raw_bytes = doc.read()
        try:
            import io
            import docx  # type: ignore
            document = docx.Document(io.BytesIO(raw_bytes))
            return "\n".join(para.text for para in document.paragraphs if para.text.strip())
        except ImportError:
            # Fall back to raw bytes decode (will be garbled but better than nothing)
            return raw_bytes.decode("utf-8", errors="ignore")

    def _verification_tool(
        self,
        draft_answer: str,
        evidence_summary: str = "",
    ) -> dict:
        """
        Verify groundedness of draft answer.
        PRIMARY: LLM judge via OpenAI (real verification).
        FALLBACK: Heuristic scoring (word overlap + disclaimer + numbers).
        """
        evidence = evidence_summary or " ".join(self._evidence_buffer)

        # ── LLM Judge (real verification) ────────────────────────────────────
        if OPENAI_AVAILABLE and self.api_key:
            try:
                client = OpenAI(api_key=self.api_key)
                judge_prompt = (
                    "You are a grounding verifier for a banking AI system.\n\n"
                    f"EVIDENCE:\n{evidence[:1200]}\n\n"
                    f"DRAFT ANSWER:\n{draft_answer[:800]}\n\n"
                    "Evaluate the draft answer strictly:\n"
                    "1. Is the answer grounded in the evidence above? (yes/partial/no)\n"
                    "2. Are any claims made without evidence support? (list them briefly)\n"
                    "3. Is a disclaimer present? (yes/no)\n"
                    "4. Confidence: High / Moderate / Low\n"
                    "5. Should the agent retry with better retrieval? (yes/no)\n\n"
                    "Respond in this exact JSON format:\n"
                    '{"grounded":"yes|partial|no","unsupported_claims":[],'
                    '"has_disclaimer":true,"confidence":"High|Moderate|Low",'
                    '"needs_retry":false,"reason":"one sentence"}'
                )
                resp = client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": judge_prompt}],
                    temperature=0.0,
                    max_tokens=200,
                )
                raw = (resp.choices[0].message.content or "").strip()
                # Strip markdown fences if present
                raw = re.sub(r"^```json\s*|\s*```$", "", raw, flags=re.MULTILINE).strip()
                verdict = json.loads(raw)
                return {
                    "status": "success",
                    "method": "llm_judge",
                    "confidence": verdict.get("confidence", "Moderate"),
                    "confidence_score": {"High": 0.9, "Moderate": 0.6, "Low": 0.3}.get(
                        verdict.get("confidence", "Moderate"), 0.6
                    ),
                    "needs_retry": verdict.get("needs_retry", False),
                    "grounded": verdict.get("grounded", "partial"),
                    "unsupported_claims": verdict.get("unsupported_claims", []),
                    "has_disclaimer": verdict.get("has_disclaimer", False),
                    "evidence_pieces_used": len(self._evidence_buffer),
                    "recommendation": verdict.get("reason", "LLM judge completed."),
                }
            except Exception:
                pass  # fall through to heuristic

        # ── Heuristic fallback ───────────────────────────────────────────────
        answer_words = set(draft_answer.lower().split())
        evidence_words = set(evidence.lower().split())
        overlap = len(answer_words & evidence_words)
        overlap_ratio = overlap / max(len(answer_words), 1)

        has_disclaimer = any(
            p in draft_answer.lower()
            for p in ["educational", "not financial advice", "not personalized", "disclaimer"]
        )
        has_numbers = bool(re.search(r"\$[\d,]+|\d+\.?\d*%|\d{4}", draft_answer))

        score = min(1.0, overlap_ratio * 2.5)
        if has_disclaimer:
            score = min(1.0, score + 0.15)
        if has_numbers:
            score = min(1.0, score + 0.10)
        if len(self._evidence_buffer) >= 3:
            score = min(1.0, score + 0.10)

        if score >= 0.75:
            confidence, needs_retry = "High", False
        elif score >= 0.45:
            confidence, needs_retry = "Moderate", False
        else:
            confidence, needs_retry = "Low", True

        return {
            "status": "success",
            "method": "heuristic",
            "confidence": confidence,
            "confidence_score": round(score, 2),
            "needs_retry": needs_retry,
            "has_disclaimer": has_disclaimer,
            "has_specific_numbers": has_numbers,
            "evidence_pieces_used": len(self._evidence_buffer),
            "recommendation": (
                "Answer appears well-grounded. Proceed."
                if not needs_retry
                else "Evidence is weak. Retrieve more specific context before finalizing."
            ),
        }

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _looks_like_investment_request(query: str) -> bool:
        text = query.lower()
        investment_terms = [
            "invest", "investment", "portfolio", "asset allocation",
            "expected return", "returns", "risk profile", "retirement",
            "stocks", "bonds", "etf", "mutual fund", "$"
        ]
        return any(term in text for term in investment_terms) and any(
            action in text for action in ["recommend", "build", "calculate", "analyze", "analyse", "allocate", "plan"]
        )

    @staticmethod
    def _requires_regulatory_retrieval(query: str) -> bool:
        text = query.lower()
        terms = [
            "regulation", "regulatory", "compliance", "jurisdiction", "kyc", "aml",
            "fdic", "rbi", "fiu", "pmla", "basel", "finra", "sec", "sar", "str",
        ]
        return any(t in text for t in terms)

    @staticmethod
    def _is_comparison_question(query: str) -> bool:
        text = query.lower()
        comparison_terms = ["compare", "difference", "vs", "versus", "contrast", "better than"]
        return any(t in text for t in comparison_terms)

    @staticmethod
    def _is_math_planning_question(query: str) -> bool:
        text = query.lower()
        math_terms = [
            "what return do i need",
            "required return",
            "can i retire",
            "how long to reach",
            "years to reach",
        ]
        return any(t in text for t in math_terms)

    @staticmethod
    def _summarise_history(history: list[dict]) -> str:
        """Return last 3 user turns as a compact summary."""
        user_turns = [m["content"] for m in history if m.get("role") == "user"]
        return " | ".join(user_turns[-3:]) if user_turns else ""

    @staticmethod
    def _score_confidence(answer: str, tools_used: list[str]) -> str:
        if not answer:
            return "Low"
        verification_ran = "verification_tool" in tools_used
        tool_count = len(tools_used)
        if verification_ran and tool_count >= 3:
            return "High"
        if tool_count >= 2:
            return "Moderate"
        return "Low"

    @staticmethod
    def _fallback(query: str, reason: str) -> dict:
        return {
            "answer": (
                f"⚠️ Agentic mode unavailable: {reason}\n\n"
                "Please ensure your OPENAI_API_KEY is set in the Space secrets. "
                "The standard RAG modes (OpenAI / Fine-Tuned / Auto) remain available."
            ),
            "trace": [{"step": "error", "label": "❌ Agent error", "detail": reason}],
            "tools_used": [],
            "confidence": "Low",
            "latency_ms": 0,
            "requires_clarification": False,
            "clarification_questions": [],
            "evidence_count": 0,
        }


# ─────────────────────────────────────────────────────────────────────────────
# KNOWLEDGE HINTS FALLBACK (used when retriever is unavailable)
# ─────────────────────────────────────────────────────────────────────────────

_KNOWLEDGE_HINTS = {
    "investor": [
        {
            "keywords": ["fdic", "insured", "deposit"],
            "text": "FDIC insures deposits up to $250,000 per depositor per insured bank.",
        },
        {
            "keywords": ["accredited", "investor", "sec"],
            "text": "SEC accredited investor: net worth > $1M (excluding primary residence) or income > $200K.",
        },
        {
            "keywords": ["capital gains", "tax", "long-term"],
            "text": "Long-term capital gains (held > 1 year) taxed at 0%, 15%, or 20% depending on income bracket.",
        },
    ],
    "regulation": [
        {
            "keywords": ["basel", "capital", "tier"],
            "text": "Basel III requires minimum CET1 ratio of 4.5%, Tier 1 of 6%, and total capital of 8%.",
        },
        {
            "keywords": ["dodd-frank", "volcker"],
            "text": "Dodd-Frank Volcker Rule prohibits proprietary trading for banks with >$10B assets.",
        },
        {
            "keywords": ["aml", "bsa", "suspicious"],
            "text": "BSA/AML requires banks to file SARs for suspicious transactions and maintain robust CDD programs.",
        },
    ],
    "compliance": [
        {
            "keywords": ["kyc", "customer", "due diligence"],
            "text": "KYC requires identity verification, beneficial ownership collection, and ongoing monitoring.",
        },
        {
            "keywords": ["fatf", "money laundering"],
            "text": "FATF 40 Recommendations set global AML/CFT standards adopted by 200+ jurisdictions.",
        },
    ],
    "general": [
        {
            "keywords": ["stress test", "federal reserve", "dfast"],
            "text": (
                "DFAST requires banks with $100B+ in assets to conduct annual stress tests. "
                "Banks $10B-$100B face supervisory stress tests. Banks under $10B are largely exempt."
            ),
        },
        {
            "keywords": ["liquidity", "lcr"],
            "text": "Basel III LCR requires banks to hold enough high-quality liquid assets to survive 30-day stress.",
        },
    ],
    "risk": [
        {
            "keywords": ["credit risk", "loan loss"],
            "text": "Credit risk is managed via CECL (Current Expected Credit Loss) provisioning under ASC 326.",
        },
        {
            "keywords": ["market risk", "var"],
            "text": "Market risk VaR models typically use 99% confidence interval over 10-day horizon per Basel requirements.",
        },
    ],
    "capital": [
        {
            "keywords": ["cet1", "capital ratio", "adequacy"],
            "text": "CET1 ratio = Common Equity Tier 1 Capital / Risk-Weighted Assets. Minimum 4.5% required under Basel III.",
        },
    ],
}


# ─────────────────────────────────────────────────────────────────────────────
# CONVENIENCE FUNCTION (called from product_runtime.py)
# ─────────────────────────────────────────────────────────────────────────────

def run_agentic_workflow(
    user_query: str,
    uploaded_files=None,
    chat_history: list[dict] | None = None,
    retriever=None,
) -> dict:
    """
    Drop-in entry point. Call this from product_runtime.py instead of
    _run_selected_model() when model_mode == "Agentic Workspace".
    """
    agent = AgenticRuntime(retriever=retriever, uploaded_docs=uploaded_files or [])
    return agent.run(user_query, chat_history=chat_history or [])
