# Agentic Workspace Upgrade — Final Updated Package

This package contains the cleaned latest files for upgrading the Banking & Finance AI Copilot into a real Agentic Workspace.

## Files

- `agentic_runtime.py` → core runtime with real OpenAI tool-calling loop, risk-profile preflight, retriever support, portfolio tools, regulatory flags, verification, and document extraction.
- `agentic_ui.py` → Streamlit trace UI and portfolio table rendering.
- `integration_patch_v3.py` → patch instructions for wiring Agentic Workspace into `product_runtime.py`.
- `requirements_agentic.txt` → additional/updated dependencies.

## Key fixes included

1. Mode name standardized as `Agentic Workspace`.
2. `run_agentic_workflow(..., retriever=retriever_obj)` is required in integration.
3. Risk-profile preflight prevents fake portfolio answers when user details are missing.
4. Explicit-risk bug fixed: risk profile alone is not enough; goal + horizon/liquidity signal are also required.
5. Retriever compatibility improved: supports `search()`, `retrieve()`, callable retrievers, and your `retrieve_shared_context()` proxy.
6. Age parsing fixed for phrases like `I am 30` and `30 years old`.
7. Python syntax check passed.

## Deployment placement

Place files as:

```text
core/agentic_runtime.py
features/agentic_ui.py
integration_patch_v3.py  # reference only; do not import in production
```

Add dependencies from `requirements_agentic.txt` into your main `requirements.txt`.

## Important test

Ask this with no prior risk history:

```text
I have $500,000 to invest. First analyze my risk profile from this conversation, then recommend a diversified banking portfolio, calculate expected returns over 10 years, and flag any regulatory restrictions I should know.
```

Expected result: the agent should pause and ask clarification questions. It should NOT invent a risk profile or create a portfolio yet.
