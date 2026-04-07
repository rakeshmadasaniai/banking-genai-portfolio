import csv
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
QUESTIONS_FILE = BASE_DIR / "questions.csv"
OUTPUT_FILE = BASE_DIR / f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

OUTPUT_FIELDS = [
    "id",
    "question",
    "latency_ms",
    "source_count",
    "grounded_flag",
    "confidence",
    "accuracy_rating",
    "notes",
]


def load_questions():
    with QUESTIONS_FILE.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def build_rows(questions):
    rows = []
    for item in questions:
        rows.append(
            {
                "id": item["id"],
                "question": item["question"],
                "latency_ms": "",
                "source_count": "",
                "grounded_flag": "",
                "confidence": "",
                "accuracy_rating": "",
                "notes": "",
            }
        )
    return rows


def write_template(rows):
    with OUTPUT_FILE.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def main():
    questions = load_questions()
    rows = build_rows(questions)
    write_template(rows)

    print("Created a 50-question evaluation sheet for the Streamlit RAG app.")
    print(f"Questions loaded: {len(rows)}")
    print(f"Results file: {OUTPUT_FILE}")
    print()
    print("Next steps:")
    print("1. Open the generated CSV.")
    print("2. Ask each question in the deployed app or local app.")
    print("3. Fill latency_ms, source_count, grounded_flag, confidence, accuracy_rating, and notes.")
    print("4. Run: python compute_metrics.py <generated_results_file>")
    print()
    print("Why this workflow:")
    print("- The deployed app is a Streamlit interface, not a stable public JSON prediction endpoint.")
    print("- This keeps the evaluation honest and aligned with the UI metrics you actually show in the app.")


if __name__ == "__main__":
    main()
