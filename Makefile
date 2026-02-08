.PHONY: help setup install dev test lint format clean docker-up docker-down

help:
	@echo "CaseCrawl - Available commands:"
	@echo ""
	@echo "Setup:"
	@echo "  make setup        - Run automated setup script"
	@echo "  make install      - Install backend dependencies"
	@echo "  make install-frontend - Install frontend dependencies"
	@echo ""
	@echo "Development:"
	@echo "  make dev          - Run backend development server"
	@echo "  make dev-frontend - Run frontend development server"
	@echo "  make worker       - Start Celery worker"
	@echo "  make beat         - Start Celery beat (scheduler)"
	@echo "  make flower       - Start Flower monitoring"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-up    - Start Docker services"
	@echo "  make docker-down  - Stop Docker services"
	@echo "  make docker-logs  - View Docker logs"
	@echo ""
	@echo "Database:"
	@echo "  make migrate      - Run database migrations"
	@echo "  make db-reset     - Reset database (WARNING: data loss)"
	@echo ""
	@echo "Testing & Quality:"
	@echo "  make test         - Run backend tests"
	@echo "  make lint         - Run linters"
	@echo "  make format       - Format code"
	@echo "  make clean        - Clean generated files"
	@echo ""
	@echo "Utilities:"
	@echo "  make all          - Start all services (Docker + Backend + Frontend)"
	@echo "  make stop         - Stop all services"

# Setup
setup:
	@echo "Running setup script..."
	@python3 setup.py

install:
	cd backend && pip install -r requirements.txt
	cd backend && pip install "numpy<2"
	cd backend && playwright install chromium

install-frontend:
	cd frontend && npm install

# Development
dev:
	@echo "Starting backend on http://localhost:18000"
	cd backend && ../venv/bin/python -m uvicorn app.main:app --reload --port 18000

dev-frontend:
	@echo "Starting frontend on http://localhost:13000"
	cd frontend && npm run dev

worker:
	@echo "Starting Celery worker..."
	cd backend && ../venv/bin/python -m celery -A app.core.celery worker --loglevel=info

beat:
	@echo "Starting Celery beat..."
	cd backend && ../venv/bin/python -m celery -A app.core.celery beat --loglevel=info

flower:
	@echo "Starting Flower on http://localhost:15555"
	cd backend && ../venv/bin/python -m celery -A app.core.celery flower --port=15555

# Docker
docker-up:
	@echo "Starting Docker services..."
	@docker compose up -d db redis
	@echo "Waiting for services to be ready..."
	@sleep 5
	@echo "Services started:"
	@echo "  - PostgreSQL: localhost:15432"
	@echo "  - Redis: localhost:16379"

docker-down:
	@echo "Stopping Docker services..."
	@docker compose down

docker-logs:
	@docker compose logs -f

docker-reset:
	@echo "WARNING: This will delete all data!"
	@read -p "Are you sure? [y/N] " confirm && [ $$confirm = y ] && docker compose down -v || echo "Cancelled"

# Database
migrate:
	cd backend && ../venv/bin/python -c "
import asyncio
import sys
sys.path.insert(0, '.')
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import get_settings
from app.models import Base

async def migrate():
    settings = get_settings()
    engine = create_async_engine(settings.database_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
    print('Migration complete!')

asyncio.run(migrate())
"

db-reset: docker-reset
	@echo "Database reset complete"

# Testing
test:
	cd backend && ../venv/bin/python -m pytest tests/ -v

test-coverage:
	cd backend && ../venv/bin/python -m pytest tests/ --cov=app --cov-report=html

# Code Quality
lint:
	cd backend && ../venv/bin/python -m flake8 app tests || true
	cd backend && ../venv/bin/python -m mypy app || true
	cd frontend && npm run lint || true

format:
	cd backend && ../venv/bin/python -m black app tests || true
	cd backend && ../venv/bin/python -m isort app tests || true

# Cleanup
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf backend/htmlcov 2>/dev/null || true
	rm -rf frontend/dist 2>/dev/null || true

# All-in-one commands
all: docker-up
	@echo "Starting all services..."
	@make -j3 dev worker dev-frontend

stop: docker-down
	@echo "All services stopped"
