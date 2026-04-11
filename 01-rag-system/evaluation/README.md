# Evaluation

This folder contains the evaluation layer for the Banking & Finance Copilot. I wanted the project to have something stronger than screenshots and one-off examples, so this folder keeps the question packs, runners, and result snapshots together in one place.

## What Is Included

- `questions.csv`
  the original 50-question evaluation sheet
- `evaluation_queries.md`
  a 120-question domain evaluation pack
- `evaluation_multilingual.md`
  a 120-question multilingual evaluation pack
- `run_eval.py`
  generates a timestamped 50-question results sheet
- `batch_eval.py`
  runs the older local batch evaluation path
- `run_eval_sets.py`
  runs the two larger markdown-based evaluation packs automatically
- `summarize_eval_sets.py`
  summarizes any generated CSV
- `results/`
  committed result snapshots from completed runs

## Why This Matters

For a product like this, the interesting question is not only whether it can answer a banking prompt once. The real question is whether it can do that repeatedly, across modes, across languages, and with results that can be inspected later.

That is why the evaluation folder is committed to the repo instead of living as a private notebook or a local-only script.

## Two Main Evaluation Packs

### 1. Domain pack

`evaluation_queries.md` contains 120 banking and compliance prompts grouped across:

- OpenAI
- Fine-Tuned
- Auto

The set covers topics such as:

- KYC
- AML
- Basel III
- FDIC
- RBI
- CECL
- payments
- credit risk

### 2. Multilingual pack

`evaluation_multilingual.md` contains 120 multilingual prompts, again grouped across:

- OpenAI
- Fine-Tuned
- Auto

The purpose here is to check how the product behaves when the same banking system is used beyond one language or one demo-friendly prompt style.

## How To Run

From `01-rag-system/evaluation`:

```bash
python run_eval_sets.py
```

This writes timestamped outputs into `results/`:

- `evaluation_queries_results_YYYYMMDD_HHMMSS.csv`
- `evaluation_queries_summary_YYYYMMDD_HHMMSS.json`
- `evaluation_multilingual_results_YYYYMMDD_HHMMSS.csv`
- `evaluation_multilingual_summary_YYYYMMDD_HHMMSS.json`

You can also run only one set:

```bash
python run_eval_sets.py --set domain
python run_eval_sets.py --set multilingual
```

To summarize any generated CSV:

```bash
python summarize_eval_sets.py results/evaluation_queries_results_YYYYMMDD_HHMMSS.csv
```

## Current Committed Result Snapshots

The latest committed snapshots in `results/` are:

- `evaluation_queries_results_20260411_125512.csv`
- `evaluation_queries_summary_20260411_125512.json`
- `evaluation_multilingual_results_20260411_125512.csv`
- `evaluation_multilingual_summary_20260411_125512.json`

## Latest Committed Summary

### Domain evaluation pack

| Metric | Result |
|---|---|
| Total prompts | 120 |
| Available evaluated rows | 80 |
| Average latency | 2037.0 ms |
| Median latency | 2036.0 ms |

### Multilingual evaluation pack

| Metric | Result |
|---|---|
| Total prompts | 120 |
| Available evaluated rows | 80 |
| Average latency | 2031.8 ms |
| Median latency | 2031.5 ms |

## What A Reviewer Should Notice

These committed snapshots are not meant to be vanity metrics. They are meant to show that:

- the question packs exist in the repo
- the runners exist in the repo
- the result files are committed in the repo
- the summaries are derived from those raw result files

The runs are also intentionally honest about backend availability. In the committed snapshot, 80 rows were available because the OpenAI path was not active in that local export. Rather than hide that, the repo keeps the CSVs and JSON files so the run is auditable.

That gives a reviewer something stronger than "trust me, I tested it." They can inspect:

- which prompts were used
- which modes were active
- which rows were unavailable
- what the measured latency looked like
- what the summary scripts report from the raw CSV

## Practical Note

These committed summaries reflect the configured local environment that was available for the run. That is why the evaluation setup keeps the raw CSV and JSON files as well as the summary. It makes the run auditable instead of relying on a single polished metric table.
