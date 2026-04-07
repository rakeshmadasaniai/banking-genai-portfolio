"""
Banking Dataset Validator & Analyzer
Validates the generated Q&A pairs for quality before fine-tuning
"""

import json
import argparse
from pathlib import Path
from collections import Counter


def load_dataset(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_pairs(pairs):
    issues = []
    for i, p in enumerate(pairs):
        if not p.get("instruction", "").strip():
            issues.append(f"  Pair {i}: Empty instruction")
        if not p.get("output", "").strip():
            issues.append(f"  Pair {i}: Empty output")
        if len(p.get("instruction", "")) < 10:
            issues.append(f"  Pair {i}: Instruction too short")
        if len(p.get("output", "")) < 20:
            issues.append(f"  Pair {i}: Output too short")
    return issues


def check_duplicates(pairs):
    questions = [p["instruction"].strip().lower() for p in pairs]
    counts = Counter(questions)
    dupes = [(q, c) for q, c in counts.items() if c > 1]
    return dupes


def analyze_length_distribution(pairs):
    q_lens = [len(p["instruction"]) for p in pairs]
    a_lens = [len(p["output"])      for p in pairs]

    def stats(lst):
        return {
            "min":  min(lst),
            "max":  max(lst),
            "avg":  sum(lst) // len(lst),
            "total": sum(lst)
        }
    return stats(q_lens), stats(a_lens)


def print_samples(pairs, n=3):
    print(f"\n  Sample pairs (first {n}):\n")
    for i, p in enumerate(pairs[:n]):
        print(f"  [{i+1}] Q: {p['instruction'][:100]}...")
        print(f"       A: {p['output'][:150]}...")
        print()


def main():
    parser = argparse.ArgumentParser(description="Validate banking Q&A dataset")
    parser.add_argument("--file", required=True, help="Path to dataset JSON file")
    args = parser.parse_args()

    if not Path(args.file).exists():
        print(f"File not found: {args.file}")
        return

    pairs = load_dataset(args.file)
    print(f"\n Validating: {args.file}")
    print(f" Total pairs: {len(pairs)}")

    # Validation
    issues = validate_pairs(pairs)
    if issues:
        print(f"\n [WARN] Found {len(issues)} issues:")
        for issue in issues[:10]:
            print(f"   {issue}")
    else:
        print("\n  All pairs passed validation!")

    # Duplicates
    dupes = check_duplicates(pairs)
    if dupes:
        print(f"\n [WARN] Found {len(dupes)} duplicate questions:")
        for q, c in dupes[:5]:
            print(f"   ({c}x) {q[:80]}...")
    else:
        print("  No duplicate questions found!")

    # Length stats
    q_stats, a_stats = analyze_length_distribution(pairs)
    print(f"\n  Question length — min:{q_stats['min']} avg:{q_stats['avg']} max:{q_stats['max']}")
    print(f"  Answer length   — min:{a_stats['min']} avg:{a_stats['avg']} max:{a_stats['max']}")

    # Samples
    print_samples(pairs)

    # HF Dataset card stats
    print("\n  Hugging Face Dataset Card Stats:")
    print(f"   - Size: {len(pairs)} instruction-response pairs")
    print(f"   - Domain: Banking & Finance (India focused)")
    print(f"   - Format: Alpaca (instruction / input / output)")
    print(f"   - Avg answer tokens (est.): ~{a_stats['avg'] // 4}")
    print(f"   - Total tokens (est.): ~{(q_stats['total'] + a_stats['total']) // 4:,}")


if __name__ == "__main__":
    main()
