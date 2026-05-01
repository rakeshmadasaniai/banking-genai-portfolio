"""
features/agentic_ui.py
======================
Renders the Agent Workspace trace panel in Streamlit.
Plug this into product_runtime.py when model_mode == "Agentic".
"""
from __future__ import annotations
import streamlit as st


# ── Step icons ────────────────────────────────────────────────────────────────

_STEP_ICONS = {
    "start":       "🧠",
    "tool_call":   "🔧",
    "observation": "📋",
    "complete":    "✅",
    "error":       "❌",
}

_TOOL_LABELS = {
    "retrieve_banking_context":   "Knowledge Base Retrieval",
    "risk_profile_tool":          "Risk Profile Analysis",
    "portfolio_builder_tool":     "Portfolio Builder",
    "return_projection_tool":     "Return Projection",
    "investor_regulation_tool":   "Investor Regulation Check",
    "compliance_classifier_tool": "Compliance Classifier",
    "document_analysis_tool":     "Document Analysis",
    "verification_tool":          "Answer Verification",
}


# ── CSS injected once ─────────────────────────────────────────────────────────

_AGENT_CSS = """
<style>
.agent-trace-shell {
    border: 0.5px solid rgba(120,120,120,0.2);
    border-radius: 14px;
    padding: 1.2rem 1.4rem;
    margin-bottom: 1.2rem;
    background: rgba(30,30,40,0.04);
}
.agent-header {
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    opacity: 0.5;
    margin-bottom: 0.8rem;
}
.trace-step {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    padding: 6px 0;
    border-bottom: 0.5px solid rgba(120,120,120,0.1);
}
.trace-step:last-child { border-bottom: none; }
.trace-icon { font-size: 14px; min-width: 20px; margin-top: 2px; }
.trace-label { font-size: 13px; font-weight: 600; }
.trace-detail { font-size: 12px; opacity: 0.6; margin-top: 2px; }
.confidence-pill {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
}
.conf-high     { background: #d4edda; color: #155724; }
.conf-moderate { background: #fff3cd; color: #856404; }
.conf-low      { background: #f8d7da; color: #721c24; }
.tool-badge {
    display: inline-block;
    background: rgba(80,80,200,0.08);
    color: rgba(80,80,200,0.9);
    border-radius: 6px;
    padding: 2px 8px;
    font-size: 11px;
    margin: 2px 3px 2px 0;
}
.agent-meta {
    display: flex;
    gap: 18px;
    margin-top: 0.8rem;
    font-size: 12px;
    opacity: 0.55;
}
.clarification-box {
    background: rgba(255,193,7,0.1);
    border: 1px solid rgba(255,193,7,0.4);
    border-radius: 10px;
    padding: 0.8rem 1rem;
    margin-top: 0.6rem;
}
</style>
"""


def render_agent_trace(result: dict) -> None:
    """
    Render the full agent trace panel.

    Parameters
    ----------
    result : dict
        The dict returned by `run_agentic_workflow()`.
    """
    st.markdown(_AGENT_CSS, unsafe_allow_html=True)

    trace        = result.get("trace", [])
    tools_used   = result.get("tools_used", [])
    confidence   = result.get("confidence", "Low")
    latency_ms   = result.get("latency_ms", 0)
    evidence_cnt = result.get("evidence_count", 0)
    clarify      = result.get("requires_clarification", False)
    clarify_qs   = result.get("clarification_questions", [])

    with st.expander("🤖 Agentic Workspace — Execution Trace", expanded=True):
        st.markdown('<div class="agent-trace-shell">', unsafe_allow_html=True)
        st.markdown('<div class="agent-header">Agentic Workspace — step-by-step trace</div>', unsafe_allow_html=True)

        # Step-by-step trace
        for step in trace:
            step_type = step.get("step", "")
            icon  = _STEP_ICONS.get(step_type, "⚙️")
            label = step.get("label", step_type)
            detail = step.get("detail", "")

            # Truncate long JSON detail for display
            if len(detail) > 280:
                detail = detail[:280] + "…"

            st.markdown(
                f"""
                <div class="trace-step">
                  <span class="trace-icon">{icon}</span>
                  <div>
                    <div class="trace-label">{label}</div>
                    <div class="trace-detail">{detail}</div>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Tools used badges
        if tools_used:
            st.markdown("**Tools used:**", unsafe_allow_html=False)
            badges = "".join(
                f'<span class="tool-badge">{_TOOL_LABELS.get(t, t)}</span>'
                for t in tools_used
            )
            st.markdown(badges, unsafe_allow_html=True)

        # Confidence + latency + evidence + verification method
        conf_class = {
            "High": "conf-high",
            "Moderate": "conf-moderate",
            "Low": "conf-low",
        }.get(confidence, "conf-low")

        # Detect verification method from trace observations
        verify_method = "heuristic"
        for step in trace:
            if "verification_tool" in step.get("label", ""):
                detail = step.get("detail", "")
                if "llm_judge" in detail:
                    verify_method = "LLM judge ✓"
                    break

        st.markdown(
            f"""
            <div class="agent-meta">
                <span>Confidence: <span class="confidence-pill {conf_class}">{confidence}</span></span>
                <span>⏱ {latency_ms:,} ms</span>
                <span>📚 {evidence_cnt} evidence pieces</span>
                <span>🔧 {len(tools_used)} tools</span>
                <span>🔍 Verified by: {verify_method}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Clarification box
        if clarify and clarify_qs:
            st.markdown(
                '<div class="clarification-box">'
                "<strong>⚠️ Clarification needed before proceeding:</strong><br>"
                + "<br>".join(f"• {q}" for q in clarify_qs)
                + "</div>",
                unsafe_allow_html=True,
            )

        st.markdown("</div>", unsafe_allow_html=True)

    # Disclaimer always shown
    st.caption(
        "⚠️ This system is for educational and portfolio use only. "
        "It is not legal, compliance, investment, or financial advice."
    )


def render_portfolio_table(result: dict) -> None:
    """
    If the agent result contains portfolio allocation data, render it as a table.
    Searches the trace observations for portfolio_builder_tool output.
    """
    import json, pandas as pd

    for step in result.get("trace", []):
        if step.get("step") == "observation" and "portfolio_builder_tool" in step.get("label", ""):
            try:
                data = json.loads(step.get("detail", "{}"))
                allocation = data.get("allocation", [])
                if allocation:
                    df = pd.DataFrame(allocation)
                    df.columns = [
                        "Asset Class", "Allocation %", "Amount (USD)",
                        "Assumed Return %", "Contribution to Weighted Return %"
                    ]
                    st.markdown("### 📊 Portfolio Allocation")
                    st.dataframe(df, use_container_width=True, hide_index=True)
                    weighted = data.get("weighted_return_pct", 0)
                    st.metric("Blended Expected Return", f"{weighted:.2f}% / year")
            except Exception:
                pass
