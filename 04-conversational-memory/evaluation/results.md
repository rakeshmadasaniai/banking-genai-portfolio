# Project 4 Execution Notes

This file records the local verification work completed for the conversational memory backend.

## Verified locally

### Health endpoint

`GET /health`

Observed response:

```text
status   : ok
sessions : 0
```

### Single-backend chat

`POST /chat`

Sample request:

```json
{
  "message": "What is Basel III?",
  "session_id": "demo-session",
  "use_memory": true
}
```

Observed response excerpt:

```text
session_id   : demo-session
response     : Basel II (2004): Three pillars framework:
               1.
turn_count   : 2
sources      : {banking_knowledge.txt}
confidence   : High
history_used : False
summary_used : False
```

### Memory follow-up

Second request on the same session:

```json
{
  "message": "What are its capital requirements?",
  "session_id": "demo-session",
  "use_memory": true
}
```

Observed response excerpt:

```text
session_id   : demo-session
response     : NATIONAL BANK REQUIREMENTS ...
turn_count   : 4
sources      : {us_banking_knowledge.txt, banking_knowledge.txt}
confidence   : High
history_used : True
summary_used : False
```

This confirms that the backend is carrying conversation state across turns.

## Current compare-path status

`POST /chat/compare` is implemented and wired into the FastAPI app. The endpoint was reached successfully during local testing, and the remaining runtime dependency was the local HF backend environment.

The compare path should be treated as:

- verified in code structure and API shape
- partially verified in local execution
- pending full end-to-end validation with the local HF backend fully loaded

## Coherence evaluation

`evaluation/coherence_eval.py` is included to measure memory-off vs memory-on coherence.

Publish the following once the script is run end to end:

| Metric | Result |
|---|---|
| Conversations tested | To be measured |
| Avg coherence score (memory off) | To be measured |
| Avg coherence score (memory on) | To be measured |
| Relative improvement | To be measured |
