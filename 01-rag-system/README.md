# Banking Finance RAG Assistant

This project is a live Retrieval-Augmented Generation (RAG) assistant for banking, finance, compliance, and regulatory question answering.

## Live Demo
[banking-finance-rag](https://huggingface.co/spaces/RakeshMadasani/banking-finance-rag)

## Screenshots
### Space overview
![RAG Space overview](screenshots/rag-space-overview.png)

### Dashboard metrics
![RAG dashboard metrics](screenshots/rag-dashboard-metrics.png)

### Low-latency answer example
Question shown:
`Explain Regulation E liability limits for unauthorized transfers?`

![RAG assistant low-latency answer](screenshots/rag-low-latency-answer.png)

## Overview
The assistant retrieves relevant context from a curated domain knowledge base and optional uploaded PDFs, then uses an LLM to generate grounded responses with source visibility.

## Stack
- Streamlit
- LangChain
- OpenAI
- FAISS
- sentence-transformers
- pypdf

## Key Features
- source-grounded banking Q&A
- PDF upload support
- streaming responses
- confidence indicators
- lightweight evaluation metrics

## Note on latency screenshots
The current screenshots in this repository reflect real app sessions and are included as product evidence. The Regulation E example shows a sub-second response path from the deployed assistant.

## Focus Areas
- AML
- KYC
- FDIC
- RBI
- Basel III
- SAR / CTR
- banking compliance
