.PHONY: help up down logs test lint build clean sync

help:
	@echo "Project OMNI — Makefile"
	@echo "  make up       — Démarrer Docker Compose"
	@echo "  make down     — Arrêter Docker Compose"
	@echo "  make logs     — Logs des services"
	@echo "  make test     — Lancer les tests"
	@echo "  make lint     — Lint + type check"
	@echo "  make build    — Build Docker images"
	@echo "  make clean    — Supprimer containers et volumes"
	@echo "  make sync     — Sync multi-plateformes (GitHub, GitLab, Jira, Notion, HF)"

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

test:
	cd src && pip install -r requirements.txt
	pytest tests/ -v --cov=src --cov-report=html

lint:
	cd src && pip install ruff mypy
	ruff check .
	mypy . --ignore-missing-imports

build:
	docker-compose build

clean:
	docker-compose down -v
	docker system prune -f

sync:
	@echo "--- Sync GitHub ---"
	bash scripts/sync-github.sh || true
	@echo "--- Sync GitLab ---"
	bash scripts/sync-gitlab.sh || true
	@echo "--- Sync Jira ---"
	bash scripts/sync-jira.sh || true
	@echo "--- Sync Notion ---"
	bash scripts/sync-notion.sh || true
	@echo "--- Sync HuggingFace ---"
	bash scripts/sync-hf.sh || true
