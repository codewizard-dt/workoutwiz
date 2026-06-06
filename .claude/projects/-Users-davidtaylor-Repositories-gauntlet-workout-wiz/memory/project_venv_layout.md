---
name: project-venv-layout
description: Python venv and pyproject.toml live in backend/, not root — how to run Python tools and what the IDE config points at
metadata:
  type: project
---

The Python package lives entirely under `backend/`. Do NOT move `pyproject.toml` or `.venv` to the repo root.

**Layout:**
- `backend/pyproject.toml` — Python manifest, `[tool.mypy]`, `[tool.pytest.ini_options]`, `[tool.setuptools]`
- `backend/.venv` — virtualenv (created by `make install`)
- `VENV := backend/.venv` in root Makefile

**IDE config (`.vscode/settings.json`)** — the chosen approach for both subprojects, without moving any files:
- Python: `python.defaultInterpreterPath` → `backend/.venv/bin/python`, `python.analysis.extraPaths: ["backend"]`
- TypeScript: `typescript.tsdk` → `frontend/node_modules/typescript/lib` (VS Code auto-discovers tsconfig.json in subdirs; this just pins the SDK version to match the build)

**Why not hoist either manifest to root:** Moving either would break their `Dockerfile.dev` (`context: ./backend` / `context: ./frontend`, both `COPY <manifest> .`), the Docker anonymous volumes (`/app/.venv`, `/app/node_modules`), and relative config paths. The polyglot-monorepo norm is each subproject owns its manifest.

**Running tools from repo root:**
- mypy: `backend/.venv/bin/mypy --config-file backend/pyproject.toml backend/app`
- pytest: `backend/.venv/bin/pytest backend/tests/`
- Makefile targets handle this automatically (`make test`, `make typecheck-py`)

**Why:** [[project_assessment]]
