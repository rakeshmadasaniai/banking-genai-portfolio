# RAG Evaluation Pack

This folder contains a simple 50-question evaluation pack for the Banking Finance RAG Assistant.

## Files

- `questions.csv` - 50 domain questions across AML, KYC, FDIC, RBI, Basel, CTR, SAR, and core banking concepts
- `results_template.csv` - template for recording latency, source count, grounded flag, confidence, and accuracy
- `run_eval.py` - generates a timestamped 50-question results CSV ready to fill during a live app pass
- `batch_eval.py` - runs an automated local batch evaluation against the same knowledge files and prompt logic used by the app
- `compute_metrics.py` - small script to summarize the completed results sheet

## How to use it

1. Generate a fresh results sheet:

```bash
python run_eval.py
```

2. Run the 50 questions through the deployed RAG app or your local app instance.
3. For each answer, record:
   - `latency_ms`
   - `source_count`
   - `grounded_flag`
   - `confidence`
   - `accuracy_rating`
4. Save the completed rows in the generated `results_*.csv` file.
5. Run:

```bash
python compute_metrics.py results_YYYYMMDD_HHMMSS.csv
```

## Automated local batch path

If you have `OPENAI_API_KEY` available locally, you can run:

```bash
python batch_eval.py
```

This uses the same `*knowledge*.txt` files, retrieval strategy, prompt templates, and confidence logic as the Streamlit app, then writes a timestamped JSON file with:

- answer text
- latency in milliseconds
- source count
- confidence label
- simple automatic quality flags

## Important note

This evaluation pack is intended to produce honest portfolio metrics. It should not be used to claim:
- sub-1 second latency
- 90%+ grounded response rate
- high accuracy

unless those numbers are actually observed from a completed run.

The deployed Hugging Face Space is a Streamlit app, so the UI-driven workflow remains the safest way to measure the exact production experience. The automated local batch path is useful for faster iteration and reproducible offline evaluation with the same source documents and prompt logic.
