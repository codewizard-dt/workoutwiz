# 019 — Python Package Setup for 1-multi-agent

> **Depends on**: none
> **Blocks**: none
> **Parallel-safe with**: none

## Objective

Create the Python project scaffold under `1-multi-agent/`: a modern `pyproject.toml`, a virtual-environment setup, and a `Makefile` with standard targets so any assessor can install and run the system with one command.

## Approach

Use `pyproject.toml` (PEP 517/518) with `hatchling` as the build backend — the modern Python standard, no `setup.py`. Pin a minimum Python version of 3.11 (required by LangGraph's type annotations). Use a plain `venv` (not Poetry or uv) to keep the assessor onboarding friction minimal. The `Makefile` exposes `install`, `run`, `test`, and `clean` targets.

## Steps

### 1. Create directory structure  <!-- agent: general-purpose -->

Create the following layout under `1-multi-agent/` (it currently contains only `ASSESSMENT.md` and `exercises.json`):

```
1-multi-agent/
├── pyproject.toml
├── Makefile
├── README.md           ← minimal stub (full README is a later task)
└── src/
    └── workout_wiz/
        └── __init__.py
```

- [x] `1-multi-agent/pyproject.toml` exists with correct content (see step 2)
- [x] `1-multi-agent/Makefile` exists with correct content (see step 3)
- [x] `1-multi-agent/src/workout_wiz/__init__.py` exists (empty or `__version__ = "0.1.0"`)
- [x] `1-multi-agent/README.md` stub exists (one-liner: "# Fitness Coaching Multi-Agent System")

### 2. Write pyproject.toml  <!-- agent: general-purpose -->

Create `1-multi-agent/pyproject.toml` with this exact content:

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "workoutwiz"
version = "0.1.0"
description = "LangGraph fitness coaching multi-agent system"
requires-python = ">=3.11"
dependencies = [
    "langgraph>=0.2",
    "langchain>=0.3",
    "langchain-anthropic>=0.3",
    "anthropic>=0.40",
    "fastapi>=0.115",
    "uvicorn[standard]>=0.32",
    "pydantic>=2.9",
    "rapidfuzz>=3.10",
    "python-dotenv>=1.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.3",
    "pytest-asyncio>=0.24",
    "httpx>=0.27",
]

[tool.hatch.build.targets.wheel]
packages = ["src/workout_wiz"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

- [x] `pyproject.toml` is valid TOML (parseable by `python -c "import tomllib; tomllib.load(open('pyproject.toml','rb'))"`)
- [x] `requires-python = ">=3.11"` is present
- [x] All six core runtime dependencies are listed (langgraph, langchain, langchain-anthropic, anthropic, fastapi, uvicorn, pydantic, rapidfuzz, python-dotenv)

### 3. Write Makefile  <!-- agent: general-purpose -->

Create `1-multi-agent/Makefile` with this content:

```makefile
.PHONY: install run test clean

VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

install:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[dev]"
	@echo "✓ Installed. Activate with: source $(VENV)/bin/activate"

run:
	$(PYTHON) -m uvicorn workout_wiz.main:app --reload --port 8001

test:
	$(VENV)/bin/pytest tests/ -v

clean:
	rm -rf $(VENV) __pycache__ .pytest_cache *.egg-info src/*.egg-info
```

- [x] `make install` creates `.venv/` and installs the package
- [x] `make run` target references `workout_wiz.main:app` (consistent with planned FastAPI entrypoint)
- [x] `make test` target runs pytest
- [x] `make clean` removes venv and caches

### 4. Verify installation  <!-- agent: general-purpose -->

From `1-multi-agent/`, run `make install` and confirm it completes without errors.

```bash
cd 1-multi-agent && make install
```

- [x] `make install` exits 0
- [x] `.venv/` directory is created
- [x] `python -c "import langgraph; import langchain; import rapidfuzz"` exits 0 inside the venv

### 5. Update .gitignore  <!-- agent: general-purpose -->

Ensure the root `.gitignore` includes entries for Python artifacts. Add if missing:

```
# Python
__pycache__/
*.py[cod]
*.egg-info/
.venv/
dist/
.pytest_cache/
```

- [x] `.gitignore` includes `.venv/` and `__pycache__/`

## Acceptance Criteria

- [x] `1-multi-agent/pyproject.toml` is valid TOML with `requires-python = ">=3.11"` and all runtime dependencies listed
- [x] `1-multi-agent/Makefile` has `install`, `run`, `test`, `clean` targets
- [x] `make install` runs from `1-multi-agent/` and exits 0
- [x] Core imports (langgraph, langchain, rapidfuzz) succeed inside the created venv
- [x] `.gitignore` covers `.venv/` and `__pycache__/`

---
**UAT**: [`.docs/uat/completed/019-python-package-setup.uat.md`](../uat/completed/019-python-package-setup.uat.md)
