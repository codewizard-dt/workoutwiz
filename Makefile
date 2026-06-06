.PHONY: install run test clean

VENV := backend/.venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

install:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -e "backend/.[dev]"
	@echo "✓ Installed. Activate with: source $(VENV)/bin/activate"

run:
	$(PYTHON) -m uvicorn app.main:app --reload --port 8000 --app-dir backend

test:
	$(VENV)/bin/pytest backend/tests/ -v

clean:
	rm -rf $(VENV) backend/__pycache__ backend/.pytest_cache backend/*.egg-info
