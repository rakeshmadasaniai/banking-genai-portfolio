import csv
import sys
from pathlib import Path
from statistics import mean


DEFAULT_RESULTS_FILE = Path(__file__).with_name("results_template.csv")


def parse_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def parse_grounded(value):
    normalized = (value or "").strip().lower()
    return normalized in {"1", "true", "yes", "y", "grounded"}


def parse_accuracy(value):
    normalized = (value or "").strip().lower()
    mapping = {
        "accurate": 1.0,
        "partial": 0.5,
        "partially accurate": 0.5,
        "inaccurate": 0.0,
    }
    return mapping.get(normalized)


def main():
    results_file = (
        Path(sys.argv[1]).expanduser().resolve()
        if len(sys.argv) > 1
        else DEFAULT_RESULTS_FILE
    )

    if not results_file.exists():
        raise SystemExit(f"Results file not found: {results_file}")

    with results_file.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    completed = [row for row in rows if (row.get("latency_ms") or "").strip()]
    if not completed:
        raise SystemExit("No completed rows found. Fill in results_template.csv first.")

    latencies = [parse_float(row["latency_ms"]) for row in completed]
    latencies = [value for value in latencies if value is not None]

    grounded = [parse_grounded(row.get("grounded_flag")) for row in completed]
    source_counts = [parse_float(row.get("source_count")) for row in completed]
    source_counts = [value for value in source_counts if value is not None]

    accuracy_scores = [parse_accuracy(row.get("accuracy_rating")) for row in completed]
    accuracy_scores = [value for value in accuracy_scores if value is not None]

    avg_latency = round(mean(latencies), 1) if latencies else 0
    grounded_rate = round(sum(grounded) / len(grounded) * 100) if grounded else 0
    avg_sources = round(mean(source_counts), 2) if source_counts else 0
    accuracy = round(mean(accuracy_scores) * 100) if accuracy_scores else None

    print("RAG evaluation summary")
    print(f"Completed questions: {len(completed)} / {len(rows)}")
    print(f"Average latency: {avg_latency} ms")
    print(f"Average sources per answer: {avg_sources}")
    print(f"Grounded response rate: {grounded_rate}%")
    if accuracy is None:
        print("Accuracy: not rated")
    else:
        print(f"User-rated accuracy: {accuracy}%")


if __name__ == "__main__":
    main()
