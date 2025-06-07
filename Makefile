.PHONY: help build up down logs test clean init-db migrate lint format security-check

# Variables
DOCKER_COMPOSE = docker-compose
PYTHON = python3
PIP = pip3

# Colors
GREEN = \033[0;32m
RED = \033[0;31m
NC = \033[0m # No Color

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  ${GREEN}%-20s${NC} %s\n", $$1, $$2}' $(MAKEFILE_LIST)

build: ## Build all services
	@echo "${GREEN}Building all services...${NC}"
	$(DOCKER_COMPOSE) build

up: ## Start all services
	@echo "${GREEN}Starting all services...${NC}"
	$(DOCKER_COMPOSE) up -d
	@echo "${GREEN}Services started! API Gateway available at http://localhost:8080${NC}"

down: ## Stop all services
	@echo "${RED}Stopping all services...${NC}"
	$(DOCKER_COMPOSE) down

logs: ## Show logs for all services
	$(DOCKER_COMPOSE) logs -f

test: ## Run all tests
	@echo "${GREEN}Running tests...${NC}"
	@echo "Testing Auth Service..."
	cd auth-service && pytest -v
	@echo "Testing User Service..."
	cd user-service && pytest -v
	@echo "Testing Map Service..."
	cd map-service && pytest -v
	@echo "Testing AI Service..."
	cd ai-service && pytest -v
	@echo "Testing Report Service..."
	cd report-service && pytest -v
	@echo "Testing API Gateway..."
	cd api-gateway && pytest -v

test-auth: ## Run auth service tests
	cd auth-service && pytest -v

test-user: ## Run user service tests
	cd user-service && pytest -v

test-map: ## Run map service tests
	cd map-service && pytest -v

test-ai: ## Run ai service tests
	cd ai-service && pytest -v

test-gateway: ## Run API gateway tests
	cd api-gateway && pytest -v

clean: ## Clean up containers, volumes, and cache
	@echo "${RED}Cleaning up...${NC}"
	$(DOCKER_COMPOSE) down -v
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +

init-db: ## Initialize databases with sample data
	@echo "${GREEN}Initializing databases...${NC}"
	$(DOCKER_COMPOSE) exec postgres psql -U user -d auth_db -f /docker-entrypoint-initdb.d/init.sql
	$(DOCKER_COMPOSE) exec mongo mongosh user_db /docker-entrypoint-initdb.d/init.js

migrate: ## Run database migrations
	@echo "${GREEN}Running migrations...${NC}"
	cd auth-service && alembic upgrade head

lint: ## Run linting on all Python files
	@echo "${GREEN}Running linters...${NC}"
	flake8 auth-service user-service api-gateway --max-line-length=100
	black --check auth-service user-service api-gateway
	isort --check-only auth-service user-service api-gateway

format: ## Format all Python files
	@echo "${GREEN}Formatting code...${NC}"
	black auth-service user-service api-gateway
	isort auth-service user-service api-gateway

security-check: ## Run security checks
	@echo "${GREEN}Running security checks...${NC}"
	bandit -r auth-service user-service api-gateway
	safety check

install-dev: ## Install development dependencies
	@echo "${GREEN}Installing development dependencies...${NC}"
	$(PIP) install -r requirements-dev.txt

monitoring-up: ## Start monitoring stack (Prometheus + Grafana)
	@echo "${GREEN}Starting monitoring stack...${NC}"
	$(DOCKER_COMPOSE) up -d prometheus grafana
	@echo "${GREEN}Grafana available at http://localhost:3000 (admin/admin)${NC}"

health-check: ## Check health of all services
	@echo "${GREEN}Checking service health...${NC}"
	@curl -s http://localhost:8080/health | jq '.' || echo "${RED}API Gateway is down${NC}"
	@curl -s http://localhost:8001/health | jq '.' || echo "${RED}Auth Service is down${NC}"
	@curl -s http://localhost:8002/health | jq '.' || echo "${RED}User Service is down${NC}"
	@curl -s http://localhost:8003/health | jq '.' || echo "${RED}Map Service is down${NC}"
	@curl -s http://localhost:8004/health | jq '.' || echo "${RED}AI Service is down${NC}"
	@curl -s http://localhost:8005/health | jq '.' || echo "${RED}Report Service is down${NC}"

dev: ## Start services in development mode with hot reload
	@echo "${GREEN}Starting in development mode...${NC}"
	ENVIRONMENT=development $(DOCKER_COMPOSE) up

prod: ## Start services in production mode
	@echo "${GREEN}Starting in production mode...${NC}"
	ENVIRONMENT=production $(DOCKER_COMPOSE) up -d

backup-db: ## Backup databases
	@echo "${GREEN}Backing up databases...${NC}"
	@mkdir -p backups
	$(DOCKER_COMPOSE) exec postgres pg_dump -U user auth_db > backups/auth_db_$(shell date +%Y%m%d_%H%M%S).sql
	$(DOCKER_COMPOSE) exec mongo mongodump --db user_db --out /backup
	@echo "${GREEN}Backup completed!${NC}"

restore-db: ## Restore databases from backup
	@echo "${GREEN}Restoring databases...${NC}"
	@echo "Available backups:"
	@ls -la backups/
	@echo "Use: docker-compose exec postgres psql -U user auth_db < backups/[backup_file]"