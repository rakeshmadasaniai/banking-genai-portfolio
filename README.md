# Banking & Finance GenAI Portfolio

**Rakesh Madasani**  
[Live Banking & Finance Copilot](https://huggingface.co/spaces/RakeshMadasani/banking-finance-rag) | [Hugging Face Profile](https://huggingface.co/RakeshMadasani) | [GitHub](https://github.com/rakeshmadasaniai/banking-genai-portfolio) | [LinkedIn](https://www.linkedin.com/in/rakesh-madasani-b217b71b0/)

This repository is the full build story behind my Banking & Finance Copilot: a live grounded AI product focused on USA and India banking, compliance, AML, KYC, FDIC, Basel III, and RBI workflows.

I did not want this to be a one-screen chatbot demo. I wanted it to behave like a real product:

- grounded on visible source material
- measurable with repeatable evaluation packs
- flexible across OpenAI, Fine-Tuned, and Auto routing
- multilingual enough for broader banking users
- strong enough to discuss as an engineering system, not just a UI

## Live Product

- **Live app:** [banking-finance-rag](https://huggingface.co/spaces/RakeshMadasani/banking-finance-rag)
- **Dataset:** [banking-finance-qa-dataset](https://huggingface.co/datasets/RakeshMadasani/banking-finance-qa-dataset)
- **Fine-tuned model:** [banking-finance-mistral-qlora](https://huggingface.co/RakeshMadasani/banking-finance-mistral-qlora)

## What This Repo Shows

| Layer | What is in the repo | Why it matters |
|---|---|---|
| Product | A live Banking & Finance Copilot | Shows a shipped, testable AI product |
| Retrieval | FAISS + banking knowledge + source cards | Keeps answers grounded and explainable |
| Data | A domain-specific QA dataset | Shows data ownership, not just prompting |
| Model | QLoRA fine-tuning workflow | Shows model adaptation beyond API usage |
| Backend | Conversational memory API | Shows system thinking and architecture depth |
| Evaluation | 120-query domain set + 120-query multilingual set | Shows repeatable measurement, not anecdotal demos |

## Where The Product Code Lives

If someone lands on this repo from GitHub first, the main product code is not hidden in a separate private service. It lives directly inside [`01-rag-system`](01-rag-system):

- [`01-rag-system/core`](01-rag-system/core)
  runtime orchestration, retrieval flow, prompts, and shared utilities
- [`01-rag-system/features`](01-rag-system/features)
  product UI, uploads, voice output, answer cards, and interaction behavior
- [`01-rag-system/models`](01-rag-system/models)
  OpenAI mode, Fine-Tuned mode, and Auto routing logic

That structure matters because I wanted the repo to read like a real product codebase, not a single README pointing to an external demo.

## How The Portfolio Evolves

This repo is one system built in layers.

### 1. Product layer

I started with the user-facing assistant in [`01-rag-system`](01-rag-system). The goal was simple: if someone asks a banking or compliance question, the product should answer clearly and show the evidence behind the answer.

### 2. Data layer

Once the first retrieval system worked, I created a banking QA dataset in [`02-qa-dataset`](02-qa-dataset) so the domain logic would not live only inside prompts and chunk text.

### 3. Model layer

Then I fine-tuned a banking-domain adapter in [`03-qlora-finetuning`](03-qlora-finetuning) to show that I can move from application wiring into actual model adaptation.

### 4. Backend layer

Finally, I added session memory and orchestration work in [`04-conversational-memory`](04-conversational-memory), which made the portfolio feel more like a real product system than a single-page demo.

## Architecture

### End-to-End System

```mermaid
flowchart LR
    A["Curated banking knowledge"] --> B["Chunking and preprocessing"]
    B --> C["Embeddings"]
    C --> D["FAISS index"]
    D --> E["Shared grounded context"]

    A --> F["Instruction dataset generation"]
    F --> G["Banking QA dataset"]
    G --> H["QLoRA fine-tuning"]
    H --> I["Published banking adapter"]

    E --> J["OpenAI path"]
    E --> K["Fine-Tuned path"]
    E --> L["Auto routing"]

    J --> M["Live Banking & Finance Copilot"]
    K --> M
    L --> M

    M --> N["Sources, confidence, latency, uploads, read aloud"]
    M --> O["Conversational memory backend"]
```

### Live Product Runtime

```mermaid
flowchart TD
    U["Question or uploaded document"] --> R["Shared retrieval"]
    R --> C["Grounded context"]
    C --> O["OpenAI mode"]
    C --> F["Fine-Tuned mode"]
    C --> A["Auto mode"]

    A --> S["Selection logic"]
    O --> X["Answer card"]
    F --> X
    S --> X

    X --> Y["Latency, confidence, sources, read aloud"]
```

## Main Product: Banking & Finance Copilot

The main product lives in [`01-rag-system`](01-rag-system).

What it does well:
- grounded banking and compliance Q&A
- OpenAI, Fine-Tuned, and Auto modes
- source-backed answers with visible evidence
- PDF, DOCX, TXT, and image upload support
- multilingual answer support
- evaluation workflows committed alongside the app

### Product Walkthrough

#### Home screen

This is the first view of the product: the live Banking & Finance Copilot shell, stable sidebar, and model modes.

![Banking Copilot home screen](01-rag-system/screenshots/banking-copilot-home-screen.png)

#### English grounded answer

This example shows a structured English answer with visible sources, latency, and confidence.

![Grounded English answer example](01-rag-system/screenshots/grounded-english-answer-example.png)

#### Telugu grounded answer

This example shows the same product answering a banking question in Telugu while keeping the same grounded answer card format.

![Grounded Telugu answer example](01-rag-system/screenshots/grounded-telugu-answer-example.png)

#### Auto routing comparison

This view shows Auto mode selecting the faster answer path while still exposing the routing comparison to the user.

![Auto routing comparison view](01-rag-system/screenshots/auto-routing-comparison-view.png)

## Evaluation

The repo includes two larger evaluation packs inside [`01-rag-system/evaluation`](01-rag-system/evaluation):

- `evaluation_queries.md`
  120 domain-specific banking, AML, KYC, Basel III, FDIC, RBI, CECL, and payments questions
- `evaluation_multilingual.md`
  120 multilingual questions grouped across OpenAI, Fine-Tuned, and Auto modes

The folder also includes:

- `run_eval_sets.py` to run both evaluation packs automatically
- `summarize_eval_sets.py` to summarize any generated CSV
- committed result snapshots in [`01-rag-system/evaluation/results`](01-rag-system/evaluation/results)
- raw CSV outputs plus JSON summaries, so the runs are inspectable rather than just summarized in prose

### Latest committed evaluation snapshots

**Domain evaluation pack**

| Metric | Result |
|---|---|
| Total prompts | 120 |
| Available evaluated rows | 80 |
| Average latency | 2037.0 ms |
| Median latency | 2036.0 ms |

**Multilingual evaluation pack**

| Metric | Result |
|---|---|
| Total prompts | 120 |
| Available evaluated rows | 80 |
| Average latency | 2031.8 ms |
| Median latency | 2031.5 ms |

### What those numbers mean

The committed snapshot is intentionally honest about the environment it was run in:

- the full packs contain 120 prompts each
- the committed run has 80 available rows because the OpenAI path was not active in that local export
- the Fine-Tuned and Auto paths still completed and produced auditable CSV/JSON artifacts

I prefer showing that reality instead of pretending every backend was active in every run. A reviewer can open the raw result files, see which rows were available, and rerun the exact same packs in a fully configured environment.

### Why I kept the raw result files

The most valuable part of the evaluation setup is not just the summary table. It is that the repo contains:

- the question packs
- the runner scripts
- the summarizer
- the committed outputs

So if someone asks, "How did you test it?" I can point to the exact prompts, exact outputs, and exact summaries rather than hand-picked screenshots.

Those results matter to me because they make the product discussable in a serious way. If someone asks how I tested it, I can point to committed query packs, reproducible runners, timestamped results, and summaries instead of hand-wavy claims.

## Other Projects In The Portfolio

### [02-qa-dataset](02-qa-dataset)

This is the dataset layer behind the banking system. It contains the curated QA data used to support model adaptation and domain coverage.

![Dataset screenshot](02-qa-dataset/screenshots/dataset-hf-splits.png)

### [03-qlora-finetuning](03-qlora-finetuning)

This is the model adaptation layer. It shows the QLoRA workflow used to adapt a Mistral model for banking-domain answers.

![QLoRA model page screenshot](03-qlora-finetuning/screenshots/model-page-demo.png)

### [04-conversational-memory](04-conversational-memory)

This is the backend layer that adds session memory, orchestration, and API structure to the broader assistant system.

## Best Entry Points In Code

If someone wants to inspect the implementation rather than just the screenshots, these are the best places to start:

- `01-rag-system/app.py`
- `01-rag-system/core/product_runtime.py`
- `01-rag-system/core/retriever.py`
- `01-rag-system/features/product_ui.py`
- `01-rag-system/models/auto_router.py`
- `01-rag-system/models/openai_mode.py`
- `01-rag-system/models/finetuned_mode.py`
- `01-rag-system/evaluation/run_eval_sets.py`
- `01-rag-system/evaluation/summarize_eval_sets.py`
- `02-qa-dataset/generate_dataset.py`
- `03-qlora-finetuning/inference_demo.py`
- `04-conversational-memory/app/main.py`
- `04-conversational-memory/app/rag_chain.py`

## Repo Structure

```text
banking-genai-portfolio/
|-- README.md
|-- 01-rag-system/
|-- 02-qa-dataset/
|-- 03-qlora-finetuning/
`-- 04-conversational-memory/
```

## Closing Note

The part I value most in this portfolio is not that it calls an LLM. It is that the repo shows the full path from idea to product: retrieval, data, model work, backend orchestration, evaluation, and a live user-facing deployment that someone can test today.
