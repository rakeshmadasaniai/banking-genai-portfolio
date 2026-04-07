# RAG Evaluation Pack

This folder contains a simple 50-question evaluation pack for the Banking Finance RAG Assistant.

## Files

- `questions.csv` - 50 domain questions across AML, KYC, FDIC, RBI, Basel, CTR, SAR, and core banking concepts
- `results_template.csv` - template for recording latency, source count, grounded flag, confidence, and accuracy
- `compute_metrics.py` - small script to summarize the completed results sheet

## How to use it

1. Run the 50 questions through the deployed RAG app or your local app instance.
2. For each answer, record:
   - `latency_ms`
   - `source_count`
   - `grounded_flag`
   - `confidence`
   - `accuracy_rating`
3. Save the completed rows in `results_template.csv`.
4. Run:

```bash
python compute_metrics.py
```

## Important note

This evaluation pack is intended to produce honest portfolio metrics. It should not be used to claim:
- sub-1 second latency
- 90%+ grounded response rate
- high accuracy

unless those numbers are actually observed from a completed run.
