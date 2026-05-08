from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from collections import Counter


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _fmt(v) -> str:
    if v is None:
        return "N/A"
    if isinstance(v, float):
        return f"{v:.2f}"
    return str(v)


def _pick(d: dict, *keys, default=None):
    for key in keys:
        if key in d and d.get(key) is not None:
            return d.get(key)
    return default


def _confidence_counts(summary: dict) -> dict:
    by_mode = summary.get("by_mode", {}) or {}
    counter: Counter[str] = Counter()
    for mode_stats in by_mode.values():
        mode_counts = (mode_stats or {}).get("confidence_counts", {}) or {}
        for label, count in mode_counts.items():
            try:
                counter[str(label)] += int(count)
            except Exception:
                continue
    return dict(counter)


def generate_report() -> Path:
    root = Path(__file__).resolve().parent
    results = root / "results"
    report_dir = root / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)

    domain_summary_path = results / "evaluation_queries_summary_20260411_125512.json"
    multilingual_summary_path = results / "evaluation_multilingual_summary_20260411_125512.json"

    if not domain_summary_path.exists() or not multilingual_summary_path.exists():
        raise FileNotFoundError("Expected committed summary JSON files were not found in evaluation/results.")

    domain = _load(domain_summary_path)
    multi = _load(multilingual_summary_path)

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    domain_total = _pick(domain, "total_rows", "completed_queries", "total_prompts")
    domain_available = _pick(domain, "available_rows")
    domain_available_ratio = (
        round((float(domain_available) / float(domain_total)), 3)
        if domain_total and domain_available is not None
        else _pick(domain, "available_ratio")
    )
    domain_conf = _pick(domain, "confidence_counts", default=None) or _confidence_counts(domain)

    multi_total = _pick(multi, "total_rows", "completed_queries", "total_prompts")
    multi_available = _pick(multi, "available_rows")
    multi_available_ratio = (
        round((float(multi_available) / float(multi_total)), 3)
        if multi_total and multi_available is not None
        else _pick(multi, "available_ratio")
    )
    multi_conf = _pick(multi, "confidence_counts", default=None) or _confidence_counts(multi)

    report = f"""# Portfolio Evaluation Report

Generated: {generated_at}

## Domain Pack Snapshot

| Metric | Value |
|---|---|
| Total Rows | {_fmt(domain_total)} |
| Available Rows | {_fmt(domain_available)} |
| Available Ratio | {_fmt(domain_available_ratio)} |
| Average Latency (ms) | {_fmt(domain.get("average_latency_ms"))} |
| Median Latency (ms) | {_fmt(domain.get("median_latency_ms"))} |
| Average Quality Score | {_fmt(_pick(domain, "average_quality_score"))} |
| Average Groundedness | {_fmt(_pick(domain, "average_groundedness"))} |

## Multilingual Pack Snapshot

| Metric | Value |
|---|---|
| Total Rows | {_fmt(multi_total)} |
| Available Rows | {_fmt(multi_available)} |
| Available Ratio | {_fmt(multi_available_ratio)} |
| Average Latency (ms) | {_fmt(multi.get("average_latency_ms"))} |
| Median Latency (ms) | {_fmt(multi.get("median_latency_ms"))} |
| Average Quality Score | {_fmt(_pick(multi, "average_quality_score"))} |
| Average Groundedness | {_fmt(_pick(multi, "average_groundedness"))} |

## Confidence Distribution (Domain)

`{domain_conf}`

## Confidence Distribution (Multilingual)

`{multi_conf}`

## Notes

- This report is generated from committed evaluation artifacts.
- To refresh after new eval runs, execute:
  - `python 01-rag-system/evaluation/generate_portfolio_report.py`
"""

    output = report_dir / "latest_portfolio_report.md"
    output.write_text(report, encoding="utf-8")
    return output


if __name__ == "__main__":
    out = generate_report()
    print(f"Saved report to: {out}")
