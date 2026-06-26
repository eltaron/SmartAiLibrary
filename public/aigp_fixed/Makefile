.PHONY: lint test build up down clean install deploy-build deploy-up deploy-down deploy-logs deploy-ps

install:
	pip install -e .

lint:
	isort --check services/ shared/ tests/
	black --check services/ shared/ tests/
	mypy services/ shared/ --strict
	ruff check services/ shared/ tests/

test:
	pytest tests/ -v --tb=short

test-coverage:
	pytest tests/ -v --cov=services --cov=shared --cov-report=html --cov-report=term

build:
	docker compose -f infra/docker-compose.yml build

up:
	docker compose -f infra/docker-compose.yml up -d

down:
	docker compose -f infra/docker-compose.yml down

logs:
	docker compose -f infra/docker-compose.yml logs -f

ps:
	docker compose -f infra/docker-compose.yml ps

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf htmlcov
	rm -rf .coverage
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true

deploy-build:
	docker compose -f infra/docker-compose.prod.yml build

deploy-up:
	docker compose -f infra/docker-compose.prod.yml up -d

deploy-down:
	docker compose -f infra/docker-compose.prod.yml down

deploy-logs:
	docker compose -f infra/docker-compose.prod.yml logs -f

deploy-ps:
	docker compose -f infra/docker-compose.prod.yml ps

help:
	@echo "Available targets:"
	@echo "  install       - Install package and dependencies"
	@echo "  lint          - Run linting tools (isort, black, mypy, ruff)"
	@echo "  test          - Run test suite"
	@echo "  test-coverage - Run tests with coverage report"
	@echo "  build         - Build Docker images (dev)"
	@echo "  up            - Start all services (dev)"
	@echo "  down          - Stop all services (dev)"
	@echo "  logs          - Tail logs from all services (dev)"
	@echo "  ps            - Show running containers (dev)"
	@echo "  deploy-build  - Build Docker images (production)"
	@echo "  deploy-up     - Start all services (production)"
	@echo "  deploy-down   - Stop all services (production)"
	@echo "  deploy-logs   - Tail logs from all services (production)"
	@echo "  deploy-ps     - Show running containers (production)"
	@echo "  clean         - Remove build artifacts and caches"