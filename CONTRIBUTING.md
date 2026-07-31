# Contributing

Thank you for contributing.

## Principles

- Prefer predictable behaviour over impressive demos.
- Never invent dates, events, deadlines, or attendees.
- Keep destructive calendar mutations behind preview and confirmation.
- Add a regression test for every fixed parsing or scheduling bug.
- Label assumptions clearly.

## Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
pytest
ruff check .
```

## Pull requests

Describe:

- the user scenario;
- the safety impact;
- tests added;
- any schema or OAuth-scope change.
