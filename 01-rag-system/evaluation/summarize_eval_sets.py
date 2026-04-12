from __future__ import annotations

import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, median


def fail(message: str) -> None:
    print(message)
    raise SystemExit(1)


def load_rows(path: Path) -> list[dict]:
    if not path.exists():
        fail(f"Results file not found: {path}")
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def to_int(value: str) -> int:
    try:
        return int(float(value))
    except Exception:
        return 0


def summarize(rows: list[dict]) -> dict:
    available_rows = [row for row in rows if row.get("available") == "yes"]
    latencies = [to_int(row["latency_ms"]) for row in available_rows]
    groundedness_scores = [float(row["groundedness_score"]) for row in available_rows if row.get("groundedness_score")]
    completeness_scores = [float(row["completeness_score"]) for row in available_rows if row.get("completeness_score")]
    quality_scores = [float(row["quality_score"]) for row in available_rows if row.get("quality_score")]
    by_mode = defaultdict(list)
    by_language = defaultdict(list)
    for row in rows:
        by_mode[row["mode_requested"]].append(row)
        by_language[row["language"]].append(row)

    return {
        "completed_rows": len(rows),
        "available_rows": len(available_rows),
        "average_latency_ms": round(mean(latencies), 1) if latencies else None,
        "median_latency_ms": round(median(latencies), 1) if latencies else None,
        "average_groundedness_score": round(mean(groundedness_scores), 3) if groundedness_scores else None,
        "average_completeness_score": round(mean(completeness_scores), 3) if completeness_scores else None,
        "average_quality_score": round(mean(quality_scores), 3) if quality_scores else None,
        "quality_band_counts": dict(Counter(row["quality_band"] for row in available_rows if row.get("quality_band"))),
        "hallucination_risk_counts": dict(Counter(row["hallucination_risk"] for row in available_rows if row.get("hallucination_risk"))),
        "by_mode": {
            mode: {
                "count": len(mode_rows),
                "available_count": len([row for row in mode_rows if row.get("available") == "yes"]),
                "average_latency_ms": round(mean(to_int(row["latency_ms"]) for row in mode_rows if row.get("available") == "yes"), 1)
                if any(row.get("available") == "yes" for row in mode_rows)
                else None,
                "median_latency_ms": round(median(to_int(row["latency_ms"]) for row in mode_rows if row.get("available") == "yes"), 1)
                if any(row.get("available") == "yes" for row in mode_rows)
                else None,
                "confidence_counts": dict(Counter(row["confidence"] for row in mode_rows if row.get("available") == "yes")),
                "quality_band_counts": dict(Counter(row["quality_band"] for row in mode_rows if row.get("available") == "yes" and row.get("quality_band"))),
                "average_quality_score": round(mean(float(row["quality_score"]) for row in mode_rows if row.get("available") == "yes" and row.get("quality_score")), 3)
                if any(row.get("available") == "yes" and row.get("quality_score") for row in mode_rows)
                else None,
            }
            for mode, mode_rows in by_mode.items()
        },
        "by_language": {
            language: {
                "count": len(language_rows),
                "available_count": len([row for row in language_rows if row.get("available") == "yes"]),
                "average_latency_ms": round(mean(to_int(row["latency_ms"]) for row in language_rows if row.get("available") == "yes"), 1)
                if any(row.get("available") == "yes" for row in language_rows)
                else None,
                "median_latency_ms": round(median(to_int(row["latency_ms"]) for row in language_rows if row.get("available") == "yes"), 1)
                if any(row.get("available") == "yes" for row in language_rows)
                else None,
            }
            for language, language_rows in by_language.items()
        },
    }


def main() -> None:
    if len(sys.argv) != 2:
        fail("Usage: python summarize_eval_sets.py <results_csv>")
    path = Path(sys.argv[1]).resolve()
    summary = summarize(load_rows(path))
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
