# Contributing

Thanks for improving the Banking & Finance AI Agent. This repository is maintained as a serious AI engineering portfolio, so changes should be small, testable, and honest about what the code supports.

## Setup

```bash
git clone https://github.com/rakeshmadasaniai/banking-genai-portfolio.git
cd banking-genai-portfolio
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r 01-rag-system/requirements.txt
```

Copy the sample environment file and fill local secrets:

```bash
copy .env.example .env
```

Never commit real API keys or tokens.

## Branching

- Use short descriptive branches.
- Prefer `feature/...`, `fix/...`, or `docs/...`.
- Keep deployment-risky changes separate from documentation-only changes.

## Testing

Run the available unit tests:

```bash
cd 01-rag-system
python -m unittest discover -s tests -p "test_*.py"
```

When changing evaluation logic, also run the relevant scripts under `01-rag-system/evaluation`.

## Pull Request Expectations

Each PR should include:

- What changed.
- Why it changed.
- How it was tested.
- Any limitations or follow-up work.

For AI behavior changes, include at least one before/after example and avoid unsupported accuracy claims.

## Code Style

- Keep Python readable and typed where practical.
- Prefer small functions over large hidden control flow.
- Add comments only where the logic is non-obvious.
- Preserve existing UI design language unless the change is explicitly a redesign.

## Documentation Style

- Use "AI agent", "grounded GenAI system", or "tool-calling AI system" when accurate.
- Avoid "AGI" or "fully autonomous" unless the implementation and evaluation clearly support that exact claim.
- Keep metrics tied to committed evaluation files.
