# UAT: Python Package Setup for 1-multi-agent

> **Source task**: [`.docs/tasks/019-python-package-setup.md`](../tasks/019-python-package-setup.md)
> **Generated**: 2026-06-04

---

## Prerequisites

- [ ] Working directory is the repo root: `/Users/davidtaylor/Repositories/gauntlet/workout-wiz`
- [ ] Python 3.11+ is available on the system (`python3 --version`)
- [ ] No pre-existing `.venv/` inside `1-multi-agent/` (run `make clean` first if needed)

---

## Shell Script Tests

These tests verify the scaffold files exist and behave correctly by running commands against the project-local directory.

### UAT-SHELL-001: Directory Structure Exists

- **Description**: Verify all required scaffold files and directories were created under `1-multi-agent/`
- **Steps**:
  1. Run the command below from the repo root
- **Command**:
  ```bash
  ls 1-multi-agent/pyproject.toml 1-multi-agent/Makefile 1-multi-agent/README.md 1-multi-agent/src/workout_wiz/__init__.py
  ```
- **Expected Result**: All four paths are printed with no "No such file or directory" errors; exit code 0
- [x] Pass <!-- 2026-06-05 -->

---

### UAT-SHELL-002: pyproject.toml Is Valid TOML

- **Description**: Verify `pyproject.toml` is parseable by Python's standard `tomllib` (no syntax errors)
- **Steps**:
  1. Run the command below from the repo root
- **Command**:
  ```bash
  python3 -c "import tomllib; tomllib.load(open('1-multi-agent/pyproject.toml','rb')); print('valid TOML')"
  ```
- **Expected Result**: Prints `valid TOML` with no exception; exit code 0
- [x] Pass <!-- 2026-06-05 -->

---

### UAT-SHELL-003: pyproject.toml Has Required Python Constraint and Dependencies

- **Description**: Verify `requires-python = ">=3.11"` and all nine runtime dependencies are declared in `pyproject.toml`
- **Steps**:
  1. Run the command below from the repo root
- **Command**:
  ```bash
  python3 -c "
import tomllib
d = tomllib.load(open('1-multi-agent/pyproject.toml','rb'))
proj = d['project']
assert proj['requires-python'] == '>=3.11', f'requires-python wrong: {proj[\"requires-python\"]}'
deps = proj['dependencies']
required = ['langgraph','langchain','langchain-anthropic','anthropic','fastapi','uvicorn','pydantic','rapidfuzz','python-dotenv']
missing = [r for r in required if not any(dep.startswith(r) for dep in deps)]
assert not missing, f'missing deps: {missing}'
print('OK: requires-python and all 9 dependencies present')
"
  ```
- **Expected Result**: Prints `OK: requires-python and all 9 dependencies present`; exit code 0
- [x] Pass <!-- 2026-06-05 -->

---

### UAT-SHELL-004: Makefile Has All Four Required Targets

- **Description**: Verify the Makefile declares `install`, `run`, `test`, and `clean` as `.PHONY` targets and references `workout_wiz.main:app` in the `run` target
- **Steps**:
  1. Run the command below from the repo root
- **Command**:
  ```bash
  python3 -c "
content = open('1-multi-agent/Makefile').read()
for target in ['install', 'run', 'test', 'clean']:
    assert f'{target}:' in content, f'missing target: {target}'
assert 'workout_wiz.main:app' in content, 'run target does not reference workout_wiz.main:app'
assert '.PHONY' in content, 'missing .PHONY declaration'
print('OK: all four targets present and run references workout_wiz.main:app')
"
  ```
- **Expected Result**: Prints `OK: all four targets present and run references workout_wiz.main:app`; exit code 0
- [x] Pass <!-- 2026-06-05 -->

---

### UAT-SHELL-005: make install Completes Successfully

- **Description**: Verify `make install` runs from `1-multi-agent/`, creates `.venv/`, and exits 0
- **Steps**:
  1. Run the command below from the repo root (takes ~30–60 s on first run)
- **Command**:
  ```bash
  cd 1-multi-agent && make install
  ```
- **Expected Result**: Exits 0; output includes `✓ Installed. Activate with: source .venv/bin/activate`; `.venv/` directory is created
- [x] Pass <!-- 2026-06-05 -->

---

### UAT-SHELL-006: Core Imports Succeed Inside the Venv

- **Description**: Verify `langgraph`, `langchain`, and `rapidfuzz` are importable inside the installed venv
- **Steps**:
  1. `make install` must have been run (UAT-SHELL-005 must pass first)
  2. Run the command below from the repo root
- **Command**:
  ```bash
  1-multi-agent/.venv/bin/python -c "import langgraph; import langchain; import rapidfuzz; print('OK: core imports succeed')"
  ```
- **Expected Result**: Prints `OK: core imports succeed`; exit code 0
- [x] Pass <!-- 2026-06-05 -->

---

### UAT-SHELL-007: Package Is Editable-Installed (workout_wiz Importable)

- **Description**: Verify the `workout_wiz` package itself is importable from within the venv (i.e., `pip install -e .` wired it correctly)
- **Steps**:
  1. `make install` must have been run (UAT-SHELL-005 must pass first)
  2. Run the command below from the repo root
- **Command**:
  ```bash
  1-multi-agent/.venv/bin/python -c "import workout_wiz; print('version:', workout_wiz.__version__)"
  ```
- **Expected Result**: Prints `version: 0.1.0`; exit code 0
- [x] Pass <!-- 2026-06-05 -->

---

### UAT-SHELL-008: .gitignore Covers .venv and __pycache__

- **Description**: Verify the root `.gitignore` contains entries for `.venv/` and `__pycache__/`
- **Steps**:
  1. Run the command below from the repo root
- **Command**:
  ```bash
  python3 -c "
content = open('.gitignore').read()
assert '.venv/' in content, '.venv/ not in .gitignore'
assert '__pycache__/' in content, '__pycache__/ not in .gitignore'
print('OK: .venv/ and __pycache__/ are both in .gitignore')
"
  ```
- **Expected Result**: Prints `OK: .venv/ and __pycache__/ are both in .gitignore`; exit code 0
- [x] Pass <!-- 2026-06-05 -->

---

## Edge Case Tests

### UAT-EDGE-001: make clean Removes .venv and Caches

- **Description**: Verify `make clean` removes the `.venv/` directory and Python caches
- **Steps**:
  1. `make install` must have been run so `.venv/` exists
  2. Run the command below from the repo root
- **Command**:
  ```bash
  cd 1-multi-agent && make clean && python3 -c "import os; assert not os.path.exists('.venv'), '.venv still exists after clean'; print('OK: .venv removed by make clean')"
  ```
- **Expected Result**: Prints `OK: .venv removed by make clean`; exit code 0
- [x] Pass <!-- 2026-06-05 -->
