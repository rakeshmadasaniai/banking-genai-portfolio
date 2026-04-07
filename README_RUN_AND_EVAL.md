# Run and Evaluation Guide

This repo links together three Hugging Face assets and now surfaces the main engineering entrypoints locally:

- `01-rag-system/app.py`
- `01-rag-system/requirements.txt`
- `01-rag-system/evaluation/compute_metrics.py`
- `02-qa-dataset/generate_dataset.py`
- `02-qa-dataset/validate_dataset.py`
- `02-qa-dataset/upload_to_hf.py`
- `03-qlora-finetuning/Banking_QLoRA_Mistral7B_updated.ipynb`
- `03-qlora-finetuning/inference_demo.py`

## Recommended recruiter review path

1. Open the main README for the portfolio overview.
2. Open `01-rag-system/README.md` for the deployed app, screenshots, and local run instructions.
3. Open `02-qa-dataset/README.md` to see how the dataset was built and published.
4. Open `03-qlora-finetuning/README.md` for the model artifact and fine-tuning summary.

## Recommended engineer review path

1. Read `01-rag-system/app.py`
2. Read `01-rag-system/evaluation/compute_metrics.py`
3. Read `02-qa-dataset/generate_dataset.py`
4. Open `03-qlora-finetuning/Banking_QLoRA_Mistral7B_updated.ipynb`
5. Run `03-qlora-finetuning/inference_demo.py`
