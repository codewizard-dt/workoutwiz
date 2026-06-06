# 020 — Install Core Dependencies and Environment Config

> **Depends on**: [019-python-package-setup](019-python-package-setup.md)
> **Blocks**: none
> **Parallel-safe with**: none

## Objective

Verify all core runtime dependencies (langgraph, langchain, langchain-anthropic, anthropic, pydantic, rapidfuzz) install cleanly in the venv created by task 019, and create the `.env.example` file with all required environment variables so assessors know what secrets to supply.

## Approach

Dependencies are declared in `pyproject.toml` (task 019). This task validates the actual install succeeds, pins known-good versions if needed, and creates the `.env.example` template. It also adds a `python-dotenv` load call to `src/workout_wiz/__init__.py` so the app picks up `.env` automatically.

## Steps

### 1. Verify dependency install  <!-- agent: general-purpose -->

From `1-multi-agent/`, activate the venv and confirm all core imports succeed:

```bash
cd 1-multi-agent
source .venv/bin/activate
python -c "
import langgraph
import langchain
import langchain_anthropic
import anthropic
import pydantic
import rapidfuzz
import fastapi
import uvicorn
print('All imports OK')
"
```

- [x] All six imports succeed (exit 0)
- [x] If any import fails, fix by adjusting the version constraint in `pyproject.toml` and re-running `make install`

### 2. Create .env.example  <!-- agent: general-purpose -->

Create `1-multi-agent/.env.example` with all required environment variables:

```dotenv
# Anthropic API — required for all LLM calls
ANTHROPIC_API_KEY=your-anthropic-api-key-here

# Model selection (optional — defaults shown)
COACH_MODEL=claude-haiku-4-5-20251001
ROUTER_MODEL=claude-haiku-4-5-20251001
GENERATOR_MODEL=claude-haiku-4-5-20251001
LOGGER_MODEL=claude-haiku-4-5-20251001

# Server config
HOST=0.0.0.0
PORT=8001
```

- [x] `1-multi-agent/.env.example` exists with `ANTHROPIC_API_KEY` entry
- [x] All four model env vars are documented with default values

### 3. Add dotenv loading to package init  <!-- agent: general-purpose -->

Edit `1-multi-agent/src/workout_wiz/__init__.py` to load `.env` at import time:

```python
from dotenv import load_dotenv

load_dotenv()

__version__ = "0.1.0"
```

- [ ] `src/workout_wiz/__init__.py` calls `load_dotenv()`

### 4. Verify .env.example is in .gitignore exclusion  <!-- agent: general-purpose -->

Ensure `.env` (not `.env.example`) is gitignored. `.env.example` should be committed.

Check root `.gitignore` contains:
```
.env
```
but NOT `.env.example`.

- [x] `.env` is in `.gitignore`
- [x] `.env.example` is NOT in `.gitignore` (it should be committed as documentation)

## Acceptance Criteria

- [x] `python -c "import langgraph; import langchain; import rapidfuzz"` exits 0 inside `.venv`
- [x] `1-multi-agent/.env.example` exists with `ANTHROPIC_API_KEY` and four model vars documented
- [x] `src/workout_wiz/__init__.py` calls `load_dotenv()`
- [x] `.env` is gitignored; `.env.example` is not

---
**UAT**: [`.docs/uat/020-install-core-dependencies.uat.md`](../uat/020-install-core-dependencies.uat.md)
