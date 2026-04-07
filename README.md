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

### 2. Banking & Finance QA Dataset
Dataset: [banking-finance-qa-dataset](https://huggingface.co/datasets/RakeshMadasani/banking-finance-qa-dataset)

A 3,002-sample Alpaca-style instruction dataset covering AML, KYC, Basel III, FDIC, RBI, compliance, and financial concepts.

### 3. Banking Finance QLoRA Fine-Tuned Model
Model: [banking-finance-mistral-qlora](https://huggingface.co/RakeshMadasani/banking-finance-mistral-qlora)

A domain-adapted Mistral-based model fine-tuned using QLoRA on the custom banking dataset.

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
