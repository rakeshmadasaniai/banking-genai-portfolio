# Roadmap

This roadmap keeps the project moving toward a stronger production-grade Banking & Finance AI Agent without overclaiming what is already implemented.

## Phase 1 - Reliability

- Fill any missing evaluation tables with reproducible result snapshots.
- Add regression tests for high-risk banking, compliance, investment, and multilingual paths.
- Improve source-grounding checks and weak-retrieval fallbacks.
- Track p50, p95, and p99 latency instead of only averages.
- Add deterministic smoke tests for the Streamlit runtime startup path.

## Phase 2 - Agentic Architecture

- Formalize a Planner -> Executor -> Verifier loop.
- Standardize tool-use traces across all agentic modes.
- Add retry policy, max-step budgets, and clear stop conditions.
- Separate "answer directly" from "act with tools" using an explicit decision layer.
- Add durable task-state persistence for long-running autonomous workflows.

## Phase 3 - Governance

- Add compliance guardrails for AML, KYC, sanctions, investment-risk, and crisis scenarios.
- Add structured audit logs for tool calls, verification decisions, and fallback paths.
- Add escalation policy for unsupported legal, compliance, or investment-advice requests.
- Add risk scoring for answers that combine regulated finance and user-specific facts.
- Create reviewer-friendly model cards and dataset cards with limitations clearly stated.

## Phase 4 - Production Hardening

- Add Docker deployment for the Streamlit app and FastAPI memory backend.
- Add CI/CD for tests, linting, and evaluation smoke checks.
- Add API documentation for the memory backend.
- Add monitoring for latency, tool failure rates, retrieval misses, and user-facing errors.
- Add versioned releases and changelogs.

## Phase 5 - Retrieval Upgrade

- Add BM25 sparse retrieval.
- Add reciprocal rank fusion between FAISS dense retrieval and BM25 sparse retrieval.
- Add retrieval ablation tests to quantify dense-only versus hybrid retrieval quality.
- Add query rewriting for difficult regulatory and multilingual prompts.

## Phase 6 - Portfolio Distribution

- Publish a concise technical write-up explaining the system design and evaluation.
- Mirror the live Hugging Face Space state into GitHub branches or releases.
- Add demo clips or GIFs that show source cards, agent trace, uploads, and voice output.
- Keep README claims tied to committed code, result files, and reproducible scripts.
