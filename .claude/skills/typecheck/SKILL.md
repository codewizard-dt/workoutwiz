# Skill: typecheck

Run strict type checks and linting across all languages in this repo.

## Usage

```
/typecheck
```

## What it does

Runs `make typecheck`, which executes both language checks in sequence:

| Target | Tools | Scope |
|--------|-------|-------|
| `make typecheck-py` | mypy (strict) + ruff | `backend/app/**` |
| `make typecheck-ts` | tsc --noEmit + eslint | `frontend/src/**` |

Exits non-zero if any check fails.

## Config locations

| Language | Config file | Key settings |
|----------|-------------|--------------|
| Python mypy | `backend/pyproject.toml` `[tool.mypy]` | `strict = true`, pydantic plugin, `follow_imports = "skip"` for LangChain/LangGraph |
| Python ruff | `backend/pyproject.toml` `[tool.ruff]` | rules F, B, UP; FastAPI `extend-immutable-calls` |
| TypeScript | `frontend/tsconfig.json` | `strict: true` |
| ESLint | `frontend/eslint.config.mjs` | `strictTypeChecked` + `stylisticTypeChecked`; shadcn/ui overrides |

## Running individual checks

```bash
make typecheck-py   # Python only
make typecheck-ts   # TypeScript only
make typecheck      # Both
```

## Known overrides & why

- `langgraph.*`, `langchain_core.*`, `langchain_anthropic.*` → `follow_imports = "skip"`: these packages have incomplete/bad stubs despite being installed; treating as `Any` is safer than fighting stub errors.
- `app.agents.*` → `disallow_untyped_decorators = false`: LangGraph `@tool` decorators are untyped.
- ESLint `no-unnecessary-condition` and `no-unnecessary-template-expression` disabled for `src/components/ui/`: shadcn/ui generates patterns that trip these rules.
- `restrict-template-expressions` set to `allowNumber: true` globally: number interpolation in JSX templates is valid.
