# Banking & Finance Agent - Week 1 to Week 6 Execution Plan

This is the exact execution map to move this project from a strong portfolio build to a world-class engineering artifact.

## Week 1 - Proof and Packaging
- Mirror complete working code and keep README in sync with live runtime.
- Publish committed evaluation snapshots and explain what is measured.
- Add architecture + runtime diagrams and concrete entry points.
- Add deterministic regression tests for decision-critical scenarios.

Deliverables:
- `README.md` updated with live architecture and evidence references.
- `01-rag-system/tests/` for critical behavior tests.
- `01-rag-system/evaluation/reports/latest_portfolio_report.md` generated from result artifacts.

## Week 2 - Agent Core Maturity
- Harden Planner/Executor/Critic behavior in `core/agentic_runtime.py`.
- Enforce retrieval-before-answer for compliance/regulatory prompts.
- Enforce decision preflight for obvious scam/structuring/sanctions patterns.
- Reduce avoidable clarification loops via action-first rules.

Deliverables:
- Decision preflight + enforcement trace.
- In-loop self-correction using verification feedback.

## Week 3 - Memory and Context Integrity
- Strengthen short-term and profile memory handling.
- Prevent cross-thread amount/profile contamination.
- Add explicit memory update + trace events.

Deliverables:
- Stable risk/profile persistence via `st.session_state`.
- Memory regression tests for multi-turn finance flows.

## Week 4 - Safety and Compliance Governance
- Add policy-first behavior for AML/KYC/sanctions escalation paths.
- Add auditable action plans for crisis prompts.
- Expand high-risk jurisdiction + threshold references in knowledge base.

Deliverables:
- Governance-ready action templates for AML crisis and sanctions review.
- Clear “educational only” and non-personalized-advice boundaries.

## Week 5 - Performance and UX Reliability
- Optimize first paint, avoid layout flicker, preserve composer stability.
- Keep response quality while reducing unnecessary tool loops.
- Validate voice/doc/pdf flows across supported languages.

Deliverables:
- Stable premium UI behavior under mode switches and mobile viewport.
- Latency breakdown report (p50/p95 where available).

## Week 6 - Distribution and Hiring Readiness
- Publish one technical write-up with architecture + eval evidence.
- Add “How to reproduce” runbook for evaluators.
- Add release notes with measurable before/after improvements.

Deliverables:
- Public narrative that maps directly to real code and metrics.
- Recruiter/CTO-ready “what this system proves” section.

## Quality Bar (Definition of Done)
- No placeholder metrics in documentation.
- Deterministic pass for critical decision tests.
- Traceable agent steps for high-risk prompts.
- Evidence-backed claims only.
