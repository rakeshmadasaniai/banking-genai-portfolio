# Banking & Finance Copilot

Banking & Finance Copilot is a grounded AI product for USA and India banking, compliance, and financial intelligence. It combines retrieval over curated banking material with multiple model paths, source-backed answer cards, uploads, multilingual support, and evaluation workflows that are committed in the repo alongside the app itself.

## Live Product

[banking-finance-rag on Hugging Face](https://huggingface.co/spaces/RakeshMadasani/banking-finance-rag)

## What This Project Is

This is the product layer of the broader portfolio. The goal was not just to make a banking chatbot answer questions. The goal was to make it behave like a product someone could open, test, trust, and discuss seriously:

- grounded answers instead of free-floating generation
- visible source support
- multiple model modes with clear routing behavior
- uploads for real user documents
- multilingual interaction
- reproducible evaluation, not just screenshots

## Where The Code Is

The live Hugging Face Space is only the deployment target. The actual product implementation is committed here in this project:

- [`core`](./core)
  retrieval orchestration, runtime flow, prompts, and shared utilities
- [`features`](./features)
  UI rendering, uploads, read-aloud, answer formatting, and user interaction
- [`models`](./models)
  OpenAI mode, Fine-Tuned mode, and Auto routing logic

That is important because I wanted the repo to stand on its own as a real product codebase, not just point outward to a demo URL.

## What The User Can Do

- ask banking, AML, KYC, FDIC, Basel III, RBI, and compliance questions
- switch between `OpenAI`, `Fine-Tuned`, and `Auto` modes
- upload PDF, DOCX, TXT, and image files
- inspect retrieved sources under each answer
- use read-aloud on the final response
- test multilingual questions

## Why The Product Is Structured This Way

Trust was the main design constraint. For finance and compliance questions, a polished answer alone is not enough. The product needs to show where the answer came from and make its behavior explainable.

That is why the app is built around:

- shared retrieval before generation
- source cards and chunk previews
- model-mode transparency
- latency and confidence visibility
- evaluation packs committed in the repository

## Model Modes

### OpenAI

This is the strongest general-purpose answer path and the most stable baseline for live testing.

### Fine-Tuned

This uses the banking-domain Mistral adapter. It is valuable when the hosted path is configured and when lower-latency or domain-style responses are desirable.

### Auto

Auto retrieves once, evaluates candidate answer paths, and selects the winner. That makes the routing logic easier to reason about than a hidden black-box switch.

## Product Architecture

```mermaid
flowchart LR
    A["Built-in banking knowledge + uploaded docs"] --> B["Chunking and preprocessing"]
    B --> C["Embeddings"]
    C --> D["FAISS retrieval"]
    D --> E["Shared grounded context"]
    E --> F["OpenAI mode"]
    E --> G["Fine-Tuned mode"]
    E --> H["Auto routing"]
    F --> I["Answer card"]
    G --> I
    H --> I
    I --> J["Sources, confidence, latency, read aloud"]
```

## How It Works

1. The app loads curated banking knowledge files and any uploaded user documents.
2. Documents are chunked and embedded.
3. FAISS retrieves the most relevant context for the question.
4. The selected model mode answers from that shared context.
5. The UI renders the answer together with:
   - mode
   - latency
   - chunk count
   - source cards
   - confidence label

## Product Walkthrough

### A clean first impression for the product

This is the opening experience of the Banking & Finance Copilot: the stable sidebar, the mode selector, the welcome guidance, and multilingual starter questions that make the product feel usable from the first click.

![Banking Copilot home experience](screenshots/banking-copilot-home-experience.png)

### A grounded English answer that feels concise and useful

This example shows the assistant answering a KYC question in English with a direct explanation, short supporting bullets, visible latency, and a retrieved source card underneath the answer.

![English KYC answer walkthrough](screenshots/english-kyc-answer-walkthrough.png)

### The same product experience working in Telugu

This screenshot matters because it shows the product doing more than translation. The answer stays structured, readable, and grounded while responding to the question naturally in Telugu.

![Telugu KYC answer walkthrough](screenshots/telugu-kyc-answer-walkthrough.png)

### Multilingual grounding working in Chinese as well

This example shows the same KYC flow in Chinese, which helps demonstrate that the product experience is consistent across languages rather than being strong only in English.

![Chinese KYC answer walkthrough](screenshots/chinese-kyc-answer-walkthrough.png)

## Evaluation

The [`evaluation`](./evaluation) folder includes two larger committed evaluation packs:

- `evaluation_queries.md`
  120 domain-specific prompts across OpenAI, Fine-Tuned, and Auto
- `evaluation_multilingual.md`
  120 multilingual prompts across the same three modes

Supporting scripts:

- `run_eval_sets.py`
- `summarize_eval_sets.py`

Latest committed result snapshots live in [`evaluation/results`](./evaluation/results).

### Latest committed summaries

| Evaluation set | Total prompts | Available evaluated rows | Average latency | Median latency |
|---|---:|---:|---:|---:|
| Domain set | 120 | 80 | 2037.0 ms | 2036.0 ms |
| Multilingual set | 120 | 80 | 2031.8 ms | 2031.5 ms |

### Reading the snapshot correctly

Those numbers are the committed run snapshot, not a made-up "best case" table:

- each pack contains 120 prompts
- 80 rows were available in the committed export
- the missing rows reflect backend availability in that local run, not missing evaluation logic

I prefer that level of honesty because anyone reviewing the repo can inspect the CSVs and JSON summaries directly and see what was measured versus what was unavailable in that environment.

## Run Locally

### Prerequisites

- Python 3.10+
- OpenAI API key

### Install

```bash
pip install -r requirements.txt
```

### Environment

```bash
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4o-mini
OPENAI_STT_MODEL=gpt-4o-mini-transcribe
OPENAI_TTS_MODEL=gpt-4o-mini-tts
OPENAI_TTS_VOICE=alloy
FINETUNED_MODEL_ID=RakeshMadasani/banking-finance-mistral-qlora
FINETUNED_ENDPOINT_URL=
HF_TOKEN=your_hugging_face_token
```

### Start the app

```bash
streamlit run app.py
```

## Notes

- Fine-Tuned mode becomes fully live when a hosted endpoint is configured. The adapter, routing logic, and evaluation path are in the repo today; the hosted endpoint is the last operational piece for a fully public demo of that mode.
- Voice input and some upload flows are still environment-sensitive because they depend on browser/runtime behavior.
- The app is built for groundedness and explainability first, not raw throughput.
