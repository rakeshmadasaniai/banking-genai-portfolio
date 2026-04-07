# Banking & Finance GenAI Portfolio

**Rakesh Madasani** · [Hugging Face](https://huggingface.co/RakeshMadasani) · [LinkedIn](https://www.linkedin.com/in/rakesh-madasani-b217b71b0/) · [Email](mailto:rakeshee230@gmail.com)

An end-to-end GenAI portfolio focused on banking, finance, compliance, and regulatory question answering.

This portfolio includes:
- a live RAG assistant for grounded banking Q&A
- a custom 3,002-sample banking instruction dataset
- a QLoRA fine-tuned Mistral model adapted to the domain

## Projects

### 1. Banking Finance RAG Assistant
Live demo: [banking-finance-rag](https://huggingface.co/spaces/RakeshMadasani/banking-finance-rag)

A deployed RAG application built with Streamlit, LangChain, FAISS, and OpenAI for source-grounded banking and compliance question answering.

**Project 1 snapshots**

Live product view, dashboard metrics, and a low-latency answer example from the deployed app:

![RAG space overview](01-rag-system/screenshots/rag-space-overview.png)

![RAG low-latency answer example](01-rag-system/screenshots/rag-low-latency-answer.png)

### 2. Banking & Finance QA Dataset
Dataset: [banking-finance-qa-dataset](https://huggingface.co/datasets/RakeshMadasani/banking-finance-qa-dataset)

A 3,002-sample Alpaca-style instruction dataset covering AML, KYC, Basel III, FDIC, RBI, compliance, and financial concepts.

**Project 2 snapshot**

Published Hugging Face dataset view showing train and validation splits:

![Dataset screenshot](02-qa-dataset/screenshots/dataset-hf-splits.png)

### 3. Banking Finance QLoRA Fine-Tuned Model
Model: [banking-finance-mistral-qlora](https://huggingface.co/RakeshMadasani/banking-finance-mistral-qlora)

A domain-adapted Mistral-based model fine-tuned using QLoRA on the custom banking dataset.

**Project 3 snapshot**

Published Hugging Face model page for the banking-domain QLoRA adapter:

![QLoRA model page screenshot](03-qlora-finetuning/screenshots/model-page-demo.png)


**Suggested live demo prompts**
- What is the FDIC deposit insurance limit in the United States?
- What are the three stages of money laundering?
- What is the difference between AML and KYC?

## Training Snapshot

| Item | Value |
|---|---|
| Base model | `mistralai/Mistral-7B-Instruct-v0.3` |
| Fine-tuning method | QLoRA |
| Training samples | 2,701 |
| Validation samples | 301 |
| Global steps | 676 |
| Final train loss | 1.13 |

## Why this portfolio matters

These projects show work across:
- application development
- retrieval pipelines
- dataset creation
- model fine-tuning
- deployment and documentation

## Comparison Snapshot

This is a qualitative comparison of the base model and the fine-tuned model on banking-domain prompts. It is meant to show the direction of improvement, not to replace a formal benchmark.

| Prompt type | Base model behavior | Fine-tuned model behavior |
|---|---|---|
| FDIC insurance questions | Usually correct, but often generic and less domain-focused | More direct, domain-specific answers with cleaner banking phrasing |
| AML / KYC concepts | Can answer broadly, but may stay high-level | More targeted banking/compliance language and stronger instructional tone |
| India-specific banking regulation | More likely to be vague or mix jurisdictions | Better alignment with RBI / banking-domain phrasing from the custom dataset |
| Compliance terminology | Understands concepts, but responses can be inconsistent | More consistent responses on SAR, CTR, Basel, AML, and KYC topics |

## Repo Structure

```text
banking-genai-portfolio/
|-- README.md
|-- 01-rag-system/
|   `-- README.md
|-- 02-qa-dataset/
|   `-- README.md
`-- 03-qlora-finetuning/
    `-- README.md
```

## Next steps
- base vs fine-tuned model comparison
- screenshots and walkthroughs
- FastAPI backend for conversational memory

## License
Apache-2.0 where applicable. See individual project repositories for details.
