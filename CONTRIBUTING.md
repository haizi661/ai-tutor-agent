# Contributing Guide

## Branching

1. Keep `main` stable and releasable.
2. Create feature branches from `main`:
   - `feat/<topic>`
   - `fix/<topic>`
   - `refactor/<topic>`
   - `docs/<topic>`

## Local Setup

```bash
pip install -e .
# or: pip install -r requirements.txt
cp .env.example .env
```

## Before Opening a PR

1. Run tests:

```bash
pytest -q
```

2. Ensure no secrets are committed (`.env`, API keys, tokens).
3. Update docs when changing architecture, state schema, or public interfaces.

## PR Rules

1. Keep PR scope focused (one concern per PR).
2. Include:
   - What changed
   - Why it changed
   - Risk and rollback notes
3. If changing graph state or event schema, update:
   - `docs/ARCHITECTURE.md`
   - `docs/PROJECT_GUIDE_ZH.md`

## Commit Message Style

Use concise prefixes:

- `feat:`
- `fix:`
- `refactor:`
- `docs:`
- `test:`
- `chore:`
