.PHONY: help install install-dev test test-cov lint format security clean docker-build docker-up docker-down docker-logs run healthcheck

help:
	@echo "Sentinel Telegram Bot - Available Tasks:"
	@echo "  make install        Install production dependencies"
	@echo "  make install-dev    Install development & CI dependencies"
	@echo "  make test           Run automated pytest test suite"
	@echo "  make test-cov       Run tests with coverage report"
	@echo "  make lint           Run code linting with flake8"
	@echo "  make format         Auto-format code with black and isort"
	@echo "  make security       Run security vulnerability scans (bandit & pip-audit)"
	@echo "  make healthcheck    Execute deployment healthcheck probe"
	@echo "  make docker-build   Build production Docker container image"
	@echo "  make docker-up      Start Docker compose stack in background"
	@echo "  make docker-down    Stop Docker compose stack"
	@echo "  make clean          Clean temporary files and caches"

install:
	python -m pip install -r requirements.txt

install-dev:
	python -m pip install -r requirements-dev.txt

test:
	python -m pytest tests/test_ci.py -v

test-cov:
	python -m pytest tests/test_ci.py --cov=core --cov=handlers --cov=database --cov-report=term-missing --cov-report=xml

lint:
	python -m flake8 core/ handlers/ ui/ tests/ scripts/ database.py config.py

format:
	python -m black core/ handlers/ ui/ tests/ scripts/ database.py config.py main.py
	python -m isort core/ handlers/ ui/ tests/ scripts/ database.py config.py main.py

security:
	python -m bandit -r core/ handlers/ database.py -ll
	python -m pip_audit

healthcheck:
	python scripts/healthcheck.py

docker-build:
	docker build -t sentinel-bot:latest .

docker-up:
	docker compose up -d

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f sentinel-bot

clean:
	rm -rf __pycache__ .pytest_cache .coverage coverage.xml
	find . -type d -name "__pycache__" -exec rm -rf {} +
