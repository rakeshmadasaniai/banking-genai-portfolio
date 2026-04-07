# Banking & Finance GenAI Portfolio

**Rakesh Madasani** | [Hugging Face](https://huggingface.co/RakeshMadasani) | [LinkedIn](https://www.linkedin.com/in/rakesh-madasani-b217b71b0/)

An end-to-end GenAI portfolio focused on banking, finance, compliance, and regulatory question answering.

This portfolio includes:
- a live RAG assistant for grounded banking Q&A
- a custom 3,002-sample banking instruction dataset
- a QLoRA fine-tuned Mistral model adapted to the domain
- a FastAPI conversational memory backend for multi-turn banking AI

## Projects

### 1. Banking Finance RAG Assistant
Live demo: [banking-finance-rag](https://huggingface.co/spaces/RakeshMadasani/banking-finance-rag)

A deployed RAG application built with Streamlit, LangChain, FAISS, and OpenAI for source-grounded banking and compliance question answering.

**Project 1 Demo**

Live product view with the app title and top-level metrics, followed by a low-latency answer example from the deployed app:

![RAG space overview](01-rag-system/screenshots/rag-space-overview.png)

![RAG low-latency answer example](01-rag-system/screenshots/rag-low-latency-answer.png)

### 2. Banking & Finance QA Dataset
Dataset: [banking-finance-qa-dataset](https://huggingface.co/datasets/RakeshMadasani/banking-finance-qa-dataset)

A 3,002-sample Alpaca-style instruction dataset covering AML, KYC, Basel III, FDIC, RBI, compliance, and financial concepts.

**Project 2 Demo**

Published Hugging Face dataset view showing train and validation splits:

![Dataset screenshot](02-qa-dataset/screenshots/dataset-hf-splits.png)

### 3. Banking Finance QLoRA Fine-Tuned Model
Model: [banking-finance-mistral-qlora](https://huggingface.co/RakeshMadasani/banking-finance-mistral-qlora)

A domain-adapted Mistral-based model fine-tuned using QLoRA on the custom banking dataset.

**Project 3 Demo**

Published Hugging Face model page for the banking-domain QLoRA adapter:

![QLoRA model page screenshot](03-qlora-finetuning/screenshots/model-page-demo.png)

**Suggested live demo prompts**
- What is the FDIC deposit insurance limit in the United States?
- What are the three stages of money laundering?
- What is the difference between AML and KYC?

### 4. Conversational Memory Backend

A FastAPI backend that wraps the banking RAG workflow with session-aware memory, history truncation, and summarization for multi-turn conversations.

**Project 4 Highlights**

- session-based memory for follow-up questions
- summarization of older turns to control prompt growth
- modular API endpoints for chat, health checks, and session clearing
- coherence evaluation scaffold for memory-on vs memory-off testing

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
- backend API design
- conversational memory management
- deployment and documentation

## Architecture

```mermaid
flowchart LR
    A["Banking and compliance documents"] --> B["Chunking and preprocessing"]
    B --> C["Banking QA dataset"]
    C --> D["QLoRA fine-tuning on Mistral-7B-Instruct"]
    D --> E["Published banking-domain adapter model"]

    A --> F["Embedding + FAISS indexing"]
    F --> G["RAG retrieval pipeline"]
    G --> H["Prompt assembly with retrieved context"]
    H --> I["Live banking RAG assistant"]
    I --> J["FastAPI conversational memory backend"]

    E -. domain knowledge strategy .-> I
```

## Comparison Snapshot

This is a qualitative comparison of the base model and the fine-tuned model on banking-domain prompts. It is meant to show the direction of improvement, not to replace a formal benchmark.

| Prompt type | Base model behavior | Fine-tuned model behavior |
|---|---|---|
| FDIC insurance questions | Usually correct, but often generic and less domain-focused | More direct, domain-specific answers with cleaner banking phrasing |
| AML / KYC concepts | Can answer broadly, but may stay high-level | More targeted banking/compliance language and stronger instructional tone |
| India-specific banking regulation | More likely to be vague or mix jurisdictions | Better alignment with RBI / banking-domain phrasing from the custom dataset |
| Compliance terminology | Understands concepts, but responses can be inconsistent | More consistent responses on SAR, CTR, Basel, AML, and KYC topics |

## Evaluation Results - RAG Assistant

A 50-question evaluation was run against the Banking Finance RAG Assistant using the local batch evaluation workflow aligned with the deployed app's retrieval and prompting logic.

| Metric | Result |
|---|---|
| Questions tested | 50 |
| Average latency | 809.3 ms |
| Average sources per answer | 1.5 |
| Grounded response rate | 92.0% |
| Has answer rate | 92.0% |

These results suggest that the assistant returns fast, mostly grounded responses on representative banking and compliance prompts, while leaving room to improve source citation visibility.

## Visible Code Entry Points

This repo now includes direct technical entrypoints rather than only project summaries:

- `01-rag-system/app.py`
- `01-rag-system/requirements.txt`
- `01-rag-system/evaluation/compute_metrics.py`
- `02-qa-dataset/generate_dataset.py`
- `02-qa-dataset/validate_dataset.py`
- `02-qa-dataset/upload_to_hf.py`
- `03-qlora-finetuning/Banking_QLoRA_Mistral7B_updated.ipynb`
- `03-qlora-finetuning/inference_demo.py`
- `04-conversational-memory/app/main.py`
- `04-conversational-memory/app/rag_chain.py`
- `04-conversational-memory/evaluation/coherence_eval.py`

## Repo Structure

```text
banking-genai-portfolio/
|-- README.md
|-- 01-rag-system/
|   `-- README.md
|-- 02-qa-dataset/
|   `-- README.md
|-- 03-qlora-finetuning/
|   `-- README.md
`-- 04-conversational-memory/
    `-- README.md
```

## Next steps
- base vs fine-tuned model comparison
- screenshots and walkthroughs
- integrated memory-on vs memory-off coherence results

## License
Apache-2.0 where applicable. See individual project repositories for details.
