# Banking & Finance Copilot Evaluation Notes

Use this file to compare the three response modes without inventing performance claims.

## Suggested checks

- Groundedness: Is the answer clearly supported by the retrieved source cards?
- Completeness: Does the answer cover the main parts of the question?
- Latency: How long did the response take in each mode?
- Source usage: How many chunks and unique sources were shown?
- Fallback quality: Did the copilot refuse unsupported questions instead of hallucinating?

## Suggested workflow

1. Run the same 25 to 50 questions through OpenAI mode.
2. Run the same set through Fine-Tuned mode once that backend is configured.
3. Run the same set through Auto mode and note which candidate won.
4. Record:
   - answer quality
   - groundedness
   - response time
   - selected model
   - whether uploaded files changed the result

## Reporting format

Create one compact table in the README with:

- mode
- avg latency
- grounded answers %
- fallback rate
- reviewer notes

Do not claim a model is better until you have measured it on the same question set.
