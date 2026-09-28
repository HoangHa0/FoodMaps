# FoodMaps developer commands. Run `make` (or `make help`) to list them.
# Requires GNU make + bash: native on Linux/macOS; on Windows use Git Bash (see docs/team/CONTRIBUTING.md).

SHELL := bash
.SHELLFLAGS := -eu -o pipefail -c
.DEFAULT_GOAL := help
.PHONY: help setup db db-down db-reset migrate migration api web dev test lint format api-types check build backup

help: ## Show this help
	@awk 'BEGIN {FS = ":.*## "} /^[a-z-]+:.*## / {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

setup: ## Install backend + frontend dependencies and create local env files
	cd backend && uv sync
	cd frontend && npm ci
	@test -f backend/.env || cp backend/.env.example backend/.env
	@test -f frontend/.env.local || cp frontend/.env.example frontend/.env.local
	@echo "Done. Next: make db && make migrate && make dev"

db: ## Start PostgreSQL 16 + PostGIS + pgvector (Docker) on localhost:5432
	docker compose up -d --build db

db-down: ## Stop the database (data is kept)
	docker compose down

db-reset: ## Delete the local database volume and recreate it (DESTROYS local data)
	docker compose down -v
	docker compose up -d --build db

migrate: ## Apply all migrations to the configured database
	cd backend && uv run alembic upgrade head

migration: ## Create a migration from model changes: make migration m="m4 add reviews table"
	@test -n "$(m)" || (echo 'Usage: make migration m="short description"' && exit 1)
	cd backend && uv run alembic revision --autogenerate -m "$(m)"

api: ## Run the backend on http://localhost:8000 (docs at /docs)
	cd backend && uv run uvicorn app.main:app --reload --port 8000

web: ## Run the frontend on http://localhost:3000
	cd frontend && npm run dev

dev: ## Run backend and frontend together (Ctrl+C stops both)
	$(MAKE) -j2 --no-print-directory api web

test: ## Run backend tests
	cd backend && uv run pytest -m "not todo"

lint: ## Lint backend (ruff) and frontend (eslint, tsc, design check)
	cd backend && uv run ruff check . && uv run ruff format --check .
	cd frontend && npm run check

format: ## Auto-fix backend formatting and lint issues
	cd backend && uv run ruff check --fix . && uv run ruff format .

api-types: ## Regenerate frontend API types after a backend schema change
	cd frontend && npm run gen:api

check: lint test ## Everything CI checks except the build: run before opening a PR
	cd backend && uv run python scripts/check_migrations.py
	@echo "All checks passed."

build: ## Production build of the frontend
	cd frontend && npm run build

backup: ## Dump a database with pg_dump in Docker: make backup url="postgresql://..."
	@test -n "$(url)" || (echo 'Usage: make backup url="postgresql://user:pass@host:5432/db"' && exit 1)
	cd backend && uv run python scripts/backup_db.py "$(url)"
