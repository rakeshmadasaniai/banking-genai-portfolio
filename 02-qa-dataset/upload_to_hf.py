"""
Upload Banking Dataset to Hugging Face Hub
Project 2: Push dataset to HF Hub as a public dataset repo
"""

import json
import os
from pathlib import Path
from datasets import Dataset, DatasetDict
from huggingface_hub import HfApi, login
from dotenv import load_dotenv

load_dotenv()

HF_TOKEN   = os.getenv("HF_TOKEN")
HF_USERNAME = os.getenv("HF_USERNAME")           # your HF username
DATASET_NAME = "banking-finance-qa-dataset"       # repo name on HF
DATA_DIR   = Path("data")


def load_splits():
    train_path = DATA_DIR / "banking_train.json"
    val_path   = DATA_DIR / "banking_val.json"

    if not train_path.exists():
        raise FileNotFoundError(f"Run generate_dataset.py first! Missing: {train_path}")

    with open(train_path) as f:
        train = json.load(f)
    with open(val_path) as f:
        val = json.load(f)

    print(f" Train: {len(train)} pairs")
    print(f" Val:   {len(val)} pairs")
    return train, val


def push_to_hub(train, val):
    login(token=HF_TOKEN)

    train_ds = Dataset.from_list(train)
    val_ds   = Dataset.from_list(val)

    dataset_dict = DatasetDict({
        "train":      train_ds,
        "validation": val_ds,
    })

    repo_id = f"{HF_USERNAME}/{DATASET_NAME}"
    print(f"\n Pushing to: https://huggingface.co/datasets/{repo_id}")

    dataset_dict.push_to_hub(
        repo_id,
        token=HF_TOKEN,
        private=False,
    )
    print(f"\n  Dataset uploaded successfully!")
    print(f"   View at: https://huggingface.co/datasets/{repo_id}")


def create_dataset_card():
    """Creates README.md for the HF dataset repo"""
    card = """---
language:
- en
license: mit
task_categories:
- text-generation
- question-answering
tags:
- banking
- finance
- india
- qlora
- instruction-tuning
- alpaca
pretty_name: Banking & Finance QA Dataset
size_categories:
- 1K<n<10K
---

# Banking & Finance Q&A Dataset

A domain-specific instruction-response dataset for fine-tuning LLMs on Indian banking and finance knowledge.

## Dataset Description

Generated using a RAG pipeline from authoritative banking documents covering:
- RBI Guidelines & Monetary Policy
- Credit Risk Management
- Loans & Lending
- KYC (Know Your Customer)
- AML (Anti-Money Laundering)
- Banking Products & Services
- Basel Norms (I, II, III)
- Financial Ratios & Analysis

## Dataset Structure

```
DatasetDict({
    train: Dataset({features: ['instruction', 'input', 'output'], ...}),
    validation: Dataset({features: ['instruction', 'input', 'output'], ...})
})
```

## Format (Alpaca)

```json
{
  "instruction": "What is the Repo Rate and what is its current value?",
  "input": "",
  "output": "The Repo Rate is the rate at which the RBI lends money to commercial banks..."
}
```

## Question Types

| Type | Description | % of dataset |
|------|-------------|-------------|
| Factual | Rates, ratios, definitions | ~45% |
| Conceptual | Explain and compare concepts | ~25% |
| Calculation | Formula-based numerical questions | ~15% |
| Application | Real-world scenarios | ~10% |
| Scenario | AML, NPA, risk case studies | ~5% |

## Usage

```python
from datasets import load_dataset

dataset = load_dataset("YOUR_USERNAME/banking-finance-qa-dataset")
train_data = dataset["train"]
```

## Fine-tuning

This dataset is designed for QLoRA fine-tuning with:
- `transformers`
- `peft`
- `trl` (SFTTrainer)
- `bitsandbytes`

## Citation

If you use this dataset, please cite:
```
@dataset{banking_finance_qa_2024,
  title={Banking & Finance Q&A Dataset},
  author={Your Name},
  year={2024},
  publisher={Hugging Face}
}
```
"""
    with open(DATA_DIR / "README.md", "w") as f:
        f.write(card)
    print(" Created README.md (Dataset Card)")


if __name__ == "__main__":
    print(" Banking Dataset → Hugging Face Hub Uploader\n")
    train, val = load_splits()
    create_dataset_card()
    push_to_hub(train, val)
