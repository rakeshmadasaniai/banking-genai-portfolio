# Evaluation

This document describes how the Banking & Finance AI Agent is evaluated and what should be improved next.

## Goals

- Measure whether answers are grounded in retrieved banking context.
- Measure latency for product responsiveness.
- Compare OpenAI, Fine-Tuned, Auto, and agentic paths where configured.
- Test multilingual behavior rather than assuming English-only quality.
- Capture failure modes openly so improvements are traceable.

## Evaluation Assets

| Asset | Location | Purpose |
|---|---|---|
| Domain query pack | `01-rag-system/evaluation/evaluation_queries.md` | Banking, AML, KYC, FDIC, RBI, Basel III, payments, and compliance prompts. |
| Multilingual query pack | `01-rag-system/evaluation/evaluation_multilingual.md` | Multilingual coverage across model modes. |
| Runner | `01-rag-system/evaluation/run_eval_sets.py` | Executes evaluation packs. |
| Summarizer | `01-rag-system/evaluation/summarize_eval_sets.py` | Produces CSV/JSON summaries. |
| Results | `01-rag-system/evaluation/results/` | Committed result snapshots. |
| Portfolio report | `01-rag-system/evaluation/reports/latest_portfolio_report.md` | Recruiter-friendly summary generated from committed artifacts. |
| Autonomy audit | `AUTONOMY_EVALUATION.md` | Honest status of the agentic/autonomous runtime. |

## Current Snapshot

| Evaluation set | Total prompts | Available evaluated rows | Average latency | Median latency |
|---|---:|---:|---:|---:|
| Domain pack | 120 | 80 | 2037.0 ms | 2036.0 ms |
| Multilingual pack | 120 | 80 | 2031.8 ms | 2031.5 ms |

The committed export includes unavailable rows where the relevant backend was not active in the local evaluation environment. This is preserved intentionally so the results stay auditable.

## Prompt Categories

- Banking definitions and explainers.
- AML/KYC/CDD/EDD compliance.
- FDIC deposit insurance.
- RBI and India banking compliance.
- Basel III capital and risk concepts.
- Payments and transaction-monitoring scenarios.
- Cross-jurisdiction comparison prompts.
- Multilingual banking questions.
- Agentic decision scenarios such as fraud, sanctions, short-horizon investing, and life-event planning.

## Groundedness Scoring

The runtime uses scoring utilities to estimate:

- overlap with retrieved documents,
- completeness of the answer,
- latency quality,
- combined candidate score for routing.

These scores are useful product signals, not formal legal or regulatory validation.

## Latency Measurement

Latency is recorded in milliseconds in model results and evaluation outputs. Current committed snapshot averages are around 2.03 seconds for available rows. Future reports should add p50, p95, p99, and per-mode latency.

## Failure Modes To Track

- Retrieval misses for narrow regulatory facts.
- Answers that ask for clarification when enough information already exists.
- Overly generic policy-generation responses.
- Cross-jurisdiction questions that need explicit table formatting.
- Voice and upload behavior that depends on browser/runtime permissions.
- Fine-Tuned mode availability when the hosted endpoint is not configured.

## Future Benchmark Plan

- Add a gold-answer set for 100 high-value banking and compliance questions.
- Add multilingual human review for at least five languages.
- Add separate benchmarks for retrieval-only, OpenAI, Fine-Tuned, Auto, and agentic modes.
- Add document-upload tests for PDF, DOCX, TXT, and image inputs.
- Add voice input/output smoke tests where runtime support is available.
- Track before/after scores for BM25/RRF once sparse retrieval is implemented.
