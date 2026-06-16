# Contributing Guide

## Branching

1. Keep `main` stable and releasable.
2. Create focused branches from `main`:
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

Fill only the vendor keys you actually need.

## Repository Hygiene

Do not commit:

- `.env`
- `data/*.db`
- `data/*.db-wal`
- `data/*.db-shm`
- `data/knowledge/*`
- `*.log`
- caches such as `.pytest_cache/`, `__pycache__/`, `.coverage`

Before opening a PR, always inspect:

```bash
git status -sb
git diff
```

## Before Opening a PR

1. Run tests:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q
```

2. Update docs when changing:
   - architecture
   - graph state
   - public API routes
   - event schema
   - model/config behavior

## PR Rules

1. Keep PR scope focused.
2. Include:
   - what changed
   - why it changed
   - validation performed
   - rollback notes if the change is risky
3. If changing graph state or event schema, update:
   - `README.md`
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
