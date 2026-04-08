# 🌎 Banking & Finance Copilot

This project is a grounded banking and finance AI copilot built with Streamlit, FAISS retrieval, OpenAI generation, and a fine-tuned model integration path. It is designed for regulatory question answering, document-assisted workflows, and product-style demo readiness.

## Live Demo
[banking-finance-rag](https://huggingface.co/spaces/RakeshMadasani/banking-finance-rag)

## Product Upgrade Highlights

- OpenAI mode for the strongest baseline RAG path
- Fine-Tuned mode wired for a banking-domain model backend
- Auto mode that compares candidates and chooses the better answer
- PDF, DOCX, and TXT upload support for session retrieval
- image upload placeholder for future OCR or vision analysis
- voice input and voice output hooks
- accessibility mode with large text, high contrast, and simplified answer display
- source-grounded response cards with response metadata

## Screenshots
### Live app overview
This screenshot shows the deployed Space header, product framing, and dashboard metrics in one view.

![RAG Space overview](screenshots/rag-space-overview.png)

### Low-latency answer example
Question shown:
`Explain Regulation E liability limits for unauthorized transfers?`

![RAG assistant low-latency answer](screenshots/rag-low-latency-answer.png)

## Overview
The copilot retrieves context from the built-in banking knowledge base plus optional uploaded documents, then routes the question through OpenAI mode, fine-tuned mode, or auto-selection mode. The answer is displayed with source cards, response metadata, and grounded fallback behavior when the retrieval signal is weak.

## Architecture

```mermaid
flowchart LR
    A["Built-in banking knowledge + uploaded docs"] --> B["Chunking and preprocessing"]
    B --> C["Embeddings with all-MiniLM-L6-v2"]
    C --> D["FAISS retrieval"]
    D --> E["Shared grounded context"]
    E --> F["OpenAI mode | Fine-Tuned mode | Auto mode"]
    F --> G["Answer + sources + confidence + metadata"]
```

## Why These Design Choices

- **FAISS for retrieval:** lightweight, fast, and easy to deploy for a focused portfolio-scale knowledge base
- **RAG over model-only answers:** keeps source grounding visible and easier to inspect during demos
- **Multiple model modes:** shows orchestration depth instead of a single fixed backend
- **Accessible UI controls:** makes the product feel more intentional and usable
- **Uploaded document support:** demonstrates document augmentation instead of relying only on static built-in knowledge

## Stack
- Streamlit
- LangChain
- OpenAI
- Hugging Face Inference Client
- FAISS
- sentence-transformers
- pypdf
- python-docx

## Code Entry Points
- `app.py` - main Streamlit application
- `core/copilot_app.py` - upgraded product-style app flow
- `core/retriever.py` - shared retrieval, upload parsing, and grounded context assembly
- `models/openai_mode.py` - OpenAI response mode
- `models/finetuned_mode.py` - fine-tuned model response mode
- `models/auto_router.py` - auto-selection logic across model candidates
- `requirements.txt` - Python dependencies for local reproduction
- `evaluation/test_questions.json` - starter evaluation set for mode comparison
- `evaluation/evaluation_notes.md` - evaluation plan and reporting notes

## Key Features
- source-grounded banking Q&A
- OpenAI, Fine-Tuned, and Auto model modes
- PDF, DOCX, and TXT upload support
- image upload placeholder
- voice-ready hooks
- accessibility options
- source cards and response metadata
- lightweight evaluation scaffolding

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
FINETUNED_MODEL_ID=RakeshMadasani/banking-finance-mistral-qlora
FINETUNED_ENDPOINT_URL=
HF_TOKEN=your_hugging_face_token
```

### Run the app

```bash
streamlit run app.py
```

### What to expect locally

On startup, the app loads the built-in banking knowledge files, builds the FAISS index, and serves the upgraded copilot UI. You can ask questions against the packaged knowledge base, upload supporting documents for session retrieval, and switch between model modes from the sidebar.

### Suggested questions
- What is the FDIC deposit insurance limit in the United States?
- What are the three stages of money laundering?
- Explain Regulation E liability limits for unauthorized transfers.
- What documents are required for KYC of an individual in India?

### Knowledge sources
The app expects the base banking knowledge files in the project directory and supports optional uploaded PDF, DOCX, and TXT documents at runtime.

## Evaluation

The repository includes a lightweight evaluation scaffold in [`evaluation`](./evaluation) with:

- starter test questions for OpenAI, Fine-Tuned, and Auto modes
- notes for comparing groundedness, completeness, latency, and fallback behavior
- a simple path for turning the copilot into a stronger benchmarked portfolio artifact

Avoid performance claims until the same questions have been run across each mode and recorded.

## Limitations

- the app depends on an external LLM backend for final answer generation
- fine-tuned mode works best when backed by a configured endpoint or supported hosted deployment
- source visibility is stronger than before, but citation styling can still improve further
- uploaded document performance depends on extraction quality and readable document text
- image and voice features are intentionally lightweight hooks in this version


## Note on latency screenshots
The current screenshots in this repository reflect real app sessions and are included as product evidence. The Regulation E example shows a sub-second response path from the deployed assistant, while the Space overview captures the main dashboard metrics in context.

## README Draft Outline

- overview
- features
- architecture
- how to run
- model modes
- screenshots
- evaluation
- roadmap
