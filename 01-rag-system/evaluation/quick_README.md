# Quick RAG Evaluation

This is a 10-question version of the evaluation pack for a fast first pass.

## Files

- `quick_questions.csv` - 10 strong representative questions
- `quick_results_template.csv` - quick results sheet

## How to run

1. Ask the 10 questions in the app.
2. Fill in `quick_results_template.csv`.
3. Run:

```bash
python compute_metrics.py quick_results_template.csv
```

## Fields to fill

- `latency_ms` - copy from the app
- `source_count` - number of sources shown
- `grounded_flag` - `yes` or `no`
- `confidence` - copy the displayed label
- `accuracy_rating` - `accurate`, `partial`, or `inaccurate`
- `notes` - short reason if needed
