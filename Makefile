.PHONY: install run test clean migrate migrate-auto migrate-down migrate-history migrate-current typecheck typecheck-py typecheck-ts eval eval-golden eval-scenarios eval-replays eval-stats

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

## typecheck-py — mypy strict + ruff lint on backend/app
typecheck-py:
	$(PYTHON) -m mypy --config-file backend/pyproject.toml backend/app
	$(VENV)/bin/ruff check backend/app

## typecheck-ts — tsc + eslint on frontend/src
typecheck-ts:
	cd frontend && npx tsc -b --noEmit
	cd frontend && npx eslint src --max-warnings=0

## typecheck — run both language checks
typecheck: typecheck-py typecheck-ts

## eval-golden — run the golden eval set against the live backend
eval-golden:
	$(PYTHON) evals/run_golden.py

## eval-scenarios — run labeled scenarios and print coverage matrix
eval-scenarios:
	$(PYTHON) evals/run_scenarios.py

## eval-replays — validate frozen replay fixtures (no API calls)
eval-replays:
	$(PYTHON) evals/run_replays.py

## eval-stats — show historical eval pass rates and trends
eval-stats:
	$(PYTHON) evals/stats.py

## eval — run golden + replays, then show stats
eval: eval-golden eval-replays eval-stats

ALEMBIC := $(VENV)/bin/alembic
ALEMBIC_DIR := backend

## migrate — apply all pending migrations (head)
migrate:
	cd $(ALEMBIC_DIR) && ../$(ALEMBIC) upgrade head

## migrate-auto — generate a new autogenerate migration (MSG required)
## Usage: make migrate-auto MSG="add users table"
migrate-auto:
	@test -n "$(MSG)" || (echo "Error: MSG is required. Usage: make migrate-auto MSG=\"your message\"" && exit 1)
	cd $(ALEMBIC_DIR) && ../$(ALEMBIC) revision --autogenerate -m "$(MSG)"

## migrate-down — downgrade by one revision
migrate-down:
	cd $(ALEMBIC_DIR) && ../$(ALEMBIC) downgrade -1

## migrate-history — show full migration history
migrate-history:
	cd $(ALEMBIC_DIR) && ../$(ALEMBIC) history --verbose

## migrate-current — show current revision
migrate-current:
	cd $(ALEMBIC_DIR) && ../$(ALEMBIC) current

# --- Docker / deployment ---

-include .env
export

GHCR_REPO   = ghcr.io/codewizard-dt/workoutwiz
DROPLET_IP ?= 167.99.234.128
PROJECT     = workoutwiz
GITHUB_USER ?= $(shell gh api user --jq .login 2>/dev/null || echo "")
RUNNER_TOKEN = $(shell gh api repos/codewizard-dt/workoutwiz/actions/runners/registration-token --jq .token 2>/dev/null)
unexport RUNNER_TOKEN
REPO_URL ?= https://github.com/codewizard-dt/workoutwiz

.PHONY: ports ps login up dev push deploy deploy-pull ssh-alias down

## ports — print all service URLs based on .env values
ports:
	@echo "Backend:  http://localhost:$(or $(BACKEND_PORT),8000)"
	@echo "Frontend: http://localhost:$(or $(FRONTEND_PORT),5173)"
	@echo "Database: localhost:$(or $(DB_PORT),5433)"

## login — authenticate Docker with GHCR (run once locally and once on the VPS)
login:
	gh auth token | docker login ghcr.io -u $(GITHUB_USER) --password-stdin

## ps — show running container status
ps:
	docker compose ps

## down — stop and remove containers
down:
	docker compose down

## dev — build from source with hot-reload bind mounts (detached)
dev:
	docker compose -f docker-compose.yml -f docker-compose.build.yml up -d --wait
	@echo "Services are running at the following URLs:"
	@echo "Backend: http://localhost:$(BACKEND_PORT)"
	@echo "Frontend: http://localhost:$(FRONTEND_PORT)"
	@echo "Database: http://localhost:$(DB_PORT)"
dev-rebuild-backend:
	docker compose -f docker-compose.yml -f docker-compose.build.yml up -d --wait --build backend frontend
	@echo "Services are running at the following URLs:"
	@echo "Backend: http://localhost:$(BACKEND_PORT)"
	@echo "Frontend: http://localhost:$(FRONTEND_PORT)"
	@echo "Database: http://localhost:$(DB_PORT)"


## up — pull latest GHCR images and start the production stack (no build)
up:
	docker compose pull && docker compose up -d --wait

## push — build linux/amd64 prod images and push to GHCR (bypasses CI)
push:
	docker buildx build --platform linux/amd64 \
		-t $(GHCR_REPO)-backend:latest --push \
		-f backend/Dockerfile.prod backend
	docker buildx build --platform linux/amd64 \
		-t $(GHCR_REPO)-frontend:latest --push \
		-f frontend/Dockerfile.prod frontend

deploy: deploy-sync
	ssh $(PROJECT) "cd /opt/$(PROJECT) && make deploy-pull"

deploy-sync:
	ssh $(PROJECT) "mkdir -p /opt/$(PROJECT)"
	scp docker-compose.yml Makefile $(PROJECT):/opt/$(PROJECT)/
	scp .env.production $(PROJECT):/opt/$(PROJECT)/.env
	scp .scripts/setup-runner.sh $(PROJECT):~/setup-runner.sh



## deploy-pull — pull new images and restart (run directly on the VPS)
deploy-pull: up

## setup-runner — upload and run the runner installer on the VPS
## Usage: make setup-runner RUNNER_TOKEN=<token>
setup-runner: deploy-sync
	ssh $(PROJECT) "RUNNER_TOKEN=$(RUNNER_TOKEN) REPO_URL=$(REPO_URL) bash ~/setup-runner.sh"

## ssh-alias — upsert ~/.ssh/config Host entry for the prod server (idempotent)
## Usage: make ssh-alias DROPLET_IP=1.2.3.4
ssh-alias:
	@mkdir -p ~/.ssh && touch ~/.ssh/config
	@if grep -q "^Host $(PROJECT)$$" ~/.ssh/config; then \
		awk 'BEGIN{found=0} /^Host $(PROJECT)$$/{found=1} found && /^[[:space:]]+HostName /{sub(/^([[:space:]]+HostName ).*/, "  HostName $(DROPLET_IP)"); found=0} {print}' \
			~/.ssh/config > /tmp/.ssh_config_tmp && mv /tmp/.ssh_config_tmp ~/.ssh/config; \
		echo "Updated: Host $(PROJECT) → $(DROPLET_IP)"; \
	else \
		printf "\nHost $(PROJECT)\n  HostName $(DROPLET_IP)\n  User root\n" >> ~/.ssh/config; \
		echo "Added: Host $(PROJECT) → $(DROPLET_IP)"; \
	fi
