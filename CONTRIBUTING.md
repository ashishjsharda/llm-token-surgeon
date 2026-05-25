# Contributing to llm-token-surgeon

First off — thank you. Every star, issue, and PR helps developers save money on LLM APIs.

## Quick start

```bash
git clone https://github.com/ashishjsharda/llm-token-surgeon
cd llm-token-surgeon
pip install -e ".[main]"
pytest
```

## What we need help with

- **New optimization techniques** — found a pattern that wastes tokens? Open a PR.
- **Provider support** — Mistral, Ollama, Cohere, Together AI.
- **Benchmarks** — run against your real prompts and share results.
- **VS Code extension** — tracked in #12.
- **Bug reports** — include the prompt (redact sensitive info) and the token counts.

## Adding a new optimization pass

1. Add a method to `Surgeon` named `_your_technique_name`
2. Return `(modified_text, ["technique_name"])` — empty list if no change
3. Call it in `Surgeon.optimize()` in the right order
4. Add a test in `tests/test_surgeon.py`
5. Add a row to the techniques table in README

## Code style

We use `ruff`. Run `ruff check --fix .` before committing.

## PR checklist

- [ ] Tests pass (`pytest`)
- [ ] Linter passes (`ruff check .`)
- [ ] README updated if adding a feature
- [ ] Added entry to CHANGELOG.md

## Reporting bugs

Open an issue with:
- Python version
- `pip show llm-token-surgeon`
- Minimal reproduction (anonymize your prompt if needed)

## License

By contributing you agree your code is MIT licensed.
