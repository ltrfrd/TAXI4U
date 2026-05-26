.PHONY: up down build migrate seed shell logs worker-logs dev

up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose build

migrate:
	docker compose run --rm backend alembic upgrade head

seed:
	docker compose run --rm backend python scripts/seed_all.py

shell:
	docker compose exec backend bash

logs:
	docker compose logs -f backend

worker-logs:
	docker compose logs -f worker

dev:
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
