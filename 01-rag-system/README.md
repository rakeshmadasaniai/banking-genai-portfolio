# Banking Finance RAG Assistant

This project is a live Retrieval-Augmented Generation (RAG) assistant for banking, finance, compliance, and regulatory question answering.

## Live Demo
[banking-finance-rag](https://huggingface.co/spaces/RakeshMadasani/banking-finance-rag)

## Screenshots
### Live app overview
This screenshot shows the deployed Space header, product framing, and dashboard metrics in one view.

![RAG Space overview](screenshots/rag-space-overview.png)

### Low-latency answer example
Question shown:
`Explain Regulation E liability limits for unauthorized transfers?`

![RAG assistant low-latency answer](screenshots/rag-low-latency-answer.png)

## Overview
The assistant retrieves relevant context from a curated domain knowledge base and optional uploaded PDFs, then uses an LLM to generate grounded responses with source visibility.

## Why These Design Choices

- **FAISS for retrieval:** lightweight, fast, and easy to deploy for a focused portfolio-scale knowledge base
- **RAG over fine-tuning-only answers:** keeps source grounding visible and easier to inspect during demos
- **Streaming responses:** improves perceived responsiveness for interactive Q&A
- **Uploaded PDF support:** demonstrates document augmentation instead of relying only on static built-in knowledge

## Stack
- Streamlit
- LangChain
- OpenAI
- FAISS
- sentence-transformers
- pypdf

## Code Entry Points
- `app.py` - main Streamlit application
- `requirements.txt` - Python dependencies for local reproduction
- `evaluation/compute_metrics.py` - simple metrics summary script for RAG evaluation
- `evaluation/questions.csv` - 50-question evaluation set
- `evaluation/quick_questions.csv` - 10-question quick evaluation set

## Key Features
- source-grounded banking Q&A
- PDF upload support
- streaming responses
- confidence indicators
- lightweight evaluation metrics

## How to Run

### Prerequisites
- Python 3.10+
- an OpenAI API key

### Install

```bash
pip install -r requirements.txt
```

### Environment

Create a `.env` file or export the variables in your shell:

```bash
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4o-mini
```

### Run the app

```bash
streamlit run app.py
```

### Suggested questions
- What is the FDIC deposit insurance limit in the United States?
- What are the three stages of money laundering?
- Explain Regulation E liability limits for unauthorized transfers.
- What documents are required for KYC of an individual in India?

### Knowledge sources
The app expects the base banking knowledge files in the project directory and supports optional uploaded PDF documents at runtime.

## Evaluation

The repository includes a lightweight evaluation framework in [`evaluation`](./evaluation) with:

- a 50-question banking-domain test set
- a 10-question quick-pass evaluation set
- a metrics script for summarizing average latency, source count, grounded response rate, and user-rated accuracy

This framework provides a simple way to assess retrieval-backed answer quality and supports future expansion into more formal benchmarking.


## Note on latency screenshots
The current screenshots in this repository reflect real app sessions and are included as product evidence. The Regulation E example shows a sub-second response path from the deployed assistant, while the Space overview captures the main dashboard metrics in context.

## Focus Areas
- AML
- KYC
- FDIC
- RBI
- Basel III
- SAR / CTR
- banking compliance
