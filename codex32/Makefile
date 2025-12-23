.PHONY: help setup install test run clean docker-remove

# Codex-32 Makefile - No Docker Required
# Provides convenient commands for development

help:
	@echo "╔════════════════════════════════════════════════════════════════╗"
	@echo "║         Codex-32 AI Orchestration System - Makefile            ║"
	@echo "╚════════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make configure          Configure environment (interactive wizard)"
	@echo "  make setup              Setup development environment"
	@echo "  make install            Install Python dependencies"
	@echo "  make db-setup           Setup PostgreSQL database"
	@echo ""
	@echo "Running:"
	@echo "  make run                Run FastAPI application (dev mode)"
	@echo "  make run-prod           Run FastAPI application (production)"
	@echo "  make serve              Start uvicorn server directly"
	@echo ""
	@echo "Bot Development:"
	@echo "  make new-bot            Create new bot from template (interactive)"
	@echo "  make list-templates     List available bot templates"
	@echo ""
	@echo "Testing:"
	@echo "  make test               Run all tests"
	@echo "  make test-unit          Run unit tests only"
	@echo "  make test-coverage      Run tests with coverage report"
	@echo ""
	@echo "Container Management:"
	@echo "  make container-list     List all containers"
	@echo "  make container-cli      Start container CLI interactive"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean              Remove temporary files and caches"
	@echo "  make format             Format code with black"
	@echo "  make lint               Lint code with flake8"
	@echo "  make type-check         Check types with mypy"
	@echo "  make docker-remove      Remove Docker/Docker Compose files (we use custom container engine)"
	@echo ""
	@echo "Documentation:"
	@echo "  make docs               Build documentation with mkdocs"
	@echo ""

configure:
	@echo "Starting configuration wizard..."
	python scripts/configure.py

setup:
	@echo "Running setup script..."
	@chmod +x setup.sh
	@./setup.sh

install:
	pip install -r requirements.txt

db-setup:
	@echo "Running database setup..."
	@chmod +x setup_database.sh
	@./setup_database.sh

run:
	@echo "Starting Codex-32 (development mode)..."
	python main.py

run-prod:
	@echo "Starting Codex-32 (production mode)..."
	uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

serve:
	uvicorn main:app --reload --host 0.0.0.0 --port 8000

new-bot:
	@echo "Creating new bot from template..."
	python scripts/init-bot.py

list-templates:
	@echo "Available bot templates:"
	@python scripts/init-bot.py --list

test:
	@echo "Running all tests..."
	pytest tests/ -v

test-unit:
	@echo "Running unit tests..."
	pytest tests/ -v -m "not integration"

test-coverage:
	@echo "Running tests with coverage..."
	pytest tests/ -v --cov=app --cov-report=html --cov-report=term

container-list:
	python -m app.container_cli list

container-cli:
	python -m app.container_cli --help

clean:
	@echo "Cleaning up temporary files..."
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -delete
	find . -type d -name '.pytest_cache' -delete
	find . -type d -name '.mypy_cache' -delete
	find . -type d -name '.coverage' -delete
	find . -type d -name 'htmlcov' -delete
	find . -type f -name '.coverage' -delete
	find . -type f -name '*.egg-info' -delete
	rm -rf dist/ build/
	@echo "✓ Cleanup complete"

format:
	@echo "Formatting code with black..."
	black app/ tests/ main.py

lint:
	@echo "Linting code with flake8..."
	flake8 app/ tests/ main.py --max-line-length=100

type-check:
	@echo "Type checking with mypy..."
	mypy app/ --ignore-missing-imports

docker-remove:
	@echo "Removing Docker-related files (using custom container engine instead)..."
	rm -f Dockerfile docker-compose.yml
	@echo "✓ Docker files removed"
	@echo "Note: Using custom container engine instead. See app/container_engine.py"

docs:
	@echo "Building documentation..."
	mkdocs build
	@echo "✓ Documentation built in site/"

.DEFAULT_GOAL := help
