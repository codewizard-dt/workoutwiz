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

# --- Docker / deployment ---

-include .env
export

GHCR_REPO   = ghcr.io/future-research/workout-wiz
DROPLET_IP ?=
PROJECT     = $(shell basename $(CURDIR))
GITHUB_USER ?= $(shell gh api user --jq .login 2>/dev/null)

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

## dev — build from source with hot-reload bind mounts
dev:
	docker compose -f docker-compose.yml -f docker-compose.build.yml up --wait

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

## deploy — sync compose file, Makefile, and .env.production to VPS then restart
deploy:
	ssh $(PROJECT) "mkdir -p /opt/$(PROJECT)"
	scp docker-compose.yml Makefile $(PROJECT):/opt/$(PROJECT)/
	scp .env.production $(PROJECT):/opt/$(PROJECT)/.env
	ssh $(PROJECT) "cd /opt/$(PROJECT) && make deploy-pull"

## deploy-pull — alias for `up`; run directly on the VPS after syncing files
deploy-pull: up

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
