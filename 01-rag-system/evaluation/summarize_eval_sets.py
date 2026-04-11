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
