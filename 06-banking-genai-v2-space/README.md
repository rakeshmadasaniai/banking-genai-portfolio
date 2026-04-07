# Banking GenAI Assistant V2 Space

This is a separate Streamlit frontend for Version B of the banking GenAI system. It intentionally keeps the same product style as the original assistant while moving answer generation and orchestration behind the FastAPI backend.

## What this app does

- preserves the familiar Version A look and feel
- calls the Version B FastAPI backend instead of handling retrieval/generation locally in the UI
- supports standard chat and compare mode
- keeps session-based conversational memory through the backend
- makes the upgraded architecture visible without breaking the baseline assistant

## Environment

Set the following environment variable in your deployment target:

```bash
BANKING_V2_API_URL=https://your-fastapi-backend-url
```

Optional:

```bash
BANKING_V2_TIMEOUT=60
```

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Why this exists separately

Version A remains the baseline deployed RAG assistant.

Version B is meant to show the upgraded engineering story:

- frontend separated from orchestration
- shared retrieval before generation
- memory-aware backend flow
- side-by-side model comparison on identical grounded context
