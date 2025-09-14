# Kali MCP Server Makefile
# Provides convenient commands for development, testing, and deployment

.PHONY: help build test clean run stop logs status setup install lint format security-scan docker-build docker-run docker-stop docker-logs docker-clean

# Default target
.DEFAULT_GOAL := help

# Variables
IMAGE_NAME := kali-mcp-server
CONTAINER_NAME := kali-mcp-server
HTTP_PORT := 5000
MCP_PORT := 8000
PYTHON := python3
PIP := pip3

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[1;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

# Help target
help: ## Show this help message
	@echo "Kali MCP Server - Available Commands"
	@echo "====================================="
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(BLUE)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""

# Development commands
setup: ## Initial setup and installation
	@echo "$(BLUE)[INFO]$(NC) Setting up Kali MCP Server..."
	@chmod +x scripts/setup.sh
	@./scripts/setup.sh setup
	@echo "$(GREEN)[SUCCESS]$(NC) Setup completed!"

install: ## Install Python dependencies
	@echo "$(BLUE)[INFO]$(NC) Installing Python dependencies..."
	@$(PIP) install -r requirements.txt
	@echo "$(GREEN)[SUCCESS]$(NC) Dependencies installed!"

# Testing commands
test: ## Run all tests
	@echo "$(BLUE)[INFO]$(NC) Running all tests..."
	@chmod +x scripts/test.sh
	@./scripts/test.sh all

test-unit: ## Run unit tests only
	@echo "$(BLUE)[INFO]$(NC) Running unit tests..."
	@chmod +x scripts/test.sh
	@./scripts/test.sh unit

test-security: ## Run security tests only
	@echo "$(BLUE)[INFO]$(NC) Running security tests..."
	@chmod +x scripts/test.sh
	@./scripts/test.sh security

test-integration: ## Run integration tests only
	@echo "$(BLUE)[INFO]$(NC) Running integration tests..."
	@chmod +x scripts/test.sh
	@./scripts/test.sh integration

test-api: ## Run API tests only
	@echo "$(BLUE)[INFO]$(NC) Running API tests..."
	@chmod +x scripts/test.sh
	@./scripts/test.sh api

test-docker: ## Run Docker tests only
	@echo "$(BLUE)[INFO]$(NC) Running Docker tests..."
	@chmod +x scripts/test.sh
	@./scripts/test.sh docker

# Code quality commands
lint: ## Run linting
	@echo "$(BLUE)[INFO]$(NC) Running linting..."
	@$(PIP) install flake8 black isort
	@flake8 server.py tests/ --max-line-length=100 --ignore=E203,W503
	@echo "$(GREEN)[SUCCESS]$(NC) Linting completed!"

format: ## Format code
	@echo "$(BLUE)[INFO]$(NC) Formatting code..."
	@$(PIP) install black isort
	@black server.py tests/ --line-length=100
	@isort server.py tests/ --profile=black
	@echo "$(GREEN)[SUCCESS]$(NC) Code formatted!"

security-scan: ## Run security scan
	@echo "$(BLUE)[INFO]$(NC) Running security scan..."
	@chmod +x scripts/test.sh
	@./scripts/test.sh scan
	@echo "$(GREEN)[SUCCESS]$(NC) Security scan completed!"

# Local development commands
run: ## Run the server locally
	@echo "$(BLUE)[INFO]$(NC) Starting Kali MCP Server locally..."
	@$(PYTHON) server.py

run-dev: ## Run the server in development mode
	@echo "$(BLUE)[INFO]$(NC) Starting Kali MCP Server in development mode..."
	@LOG_LEVEL=DEBUG $(PYTHON) server.py

# Docker commands
docker-build: ## Build Docker image
	@echo "$(BLUE)[INFO]$(NC) Building Docker image..."
	@docker build -t $(IMAGE_NAME) .
	@echo "$(GREEN)[SUCCESS]$(NC) Docker image built!"

docker-run: ## Run Docker container
	@echo "$(BLUE)[INFO]$(NC) Starting Docker container..."
	@docker run -d \
		--name $(CONTAINER_NAME) \
		-p $(HTTP_PORT):5000 \
		-p $(MCP_PORT):8000 \
		-e MAX_TIMEOUT=300 \
		-e DEFAULT_TIMEOUT=60 \
		$(IMAGE_NAME)
	@echo "$(GREEN)[SUCCESS]$(NC) Docker container started!"
	@echo "$(YELLOW)[INFO]$(NC) HTTP API: http://localhost:$(HTTP_PORT)"
	@echo "$(YELLOW)[INFO]$(NC) MCP Server: localhost:$(MCP_PORT)"

docker-stop: ## Stop Docker container
	@echo "$(BLUE)[INFO]$(NC) Stopping Docker container..."
	@docker stop $(CONTAINER_NAME) 2>/dev/null || true
	@docker rm $(CONTAINER_NAME) 2>/dev/null || true
	@echo "$(GREEN)[SUCCESS]$(NC) Docker container stopped!"

docker-logs: ## Show Docker container logs
	@echo "$(BLUE)[INFO]$(NC) Showing Docker container logs..."
	@docker logs -f $(CONTAINER_NAME)

docker-restart: docker-stop docker-run ## Restart Docker container

# Docker Compose commands
compose-up: ## Start with Docker Compose
	@echo "$(BLUE)[INFO]$(NC) Starting with Docker Compose..."
	@docker-compose up -d
	@echo "$(GREEN)[SUCCESS]$(NC) Services started!"

compose-down: ## Stop Docker Compose services
	@echo "$(BLUE)[INFO]$(NC) Stopping Docker Compose services..."
	@docker-compose down
	@echo "$(GREEN)[SUCCESS]$(NC) Services stopped!"

compose-logs: ## Show Docker Compose logs
	@echo "$(BLUE)[INFO]$(NC) Showing Docker Compose logs..."
	@docker-compose logs -f

compose-restart: compose-down compose-up ## Restart Docker Compose services

# Status and monitoring commands
status: ## Show server status
	@echo "$(BLUE)[INFO]$(NC) Checking server status..."
	@if docker ps | grep -q $(CONTAINER_NAME); then \
		echo "$(GREEN)[SUCCESS]$(NC) Server is running"; \
		docker ps | grep $(CONTAINER_NAME); \
	else \
		echo "$(YELLOW)[WARNING]$(NC) Server is not running"; \
	fi

logs: ## Show server logs
	@echo "$(BLUE)[INFO]$(NC) Showing server logs..."
	@if docker ps | grep -q $(CONTAINER_NAME); then \
		docker logs -f $(CONTAINER_NAME); \
	else \
		echo "$(YELLOW)[WARNING]$(NC) Server is not running"; \
	fi

health: ## Check server health
	@echo "$(BLUE)[INFO]$(NC) Checking server health..."
	@if curl -f http://localhost:$(HTTP_PORT)/health >/dev/null 2>&1; then \
		echo "$(GREEN)[SUCCESS]$(NC) Server is healthy"; \
	else \
		echo "$(RED)[ERROR]$(NC) Server is not responding"; \
	fi

# Cleanup commands
clean: ## Clean up local files
	@echo "$(BLUE)[INFO]$(NC) Cleaning up local files..."
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "__pycache__" -delete
	@find . -type f -name "*.log" -delete
	@rm -rf .pytest_cache/
	@rm -rf htmlcov/
	@rm -rf .coverage
	@echo "$(GREEN)[SUCCESS]$(NC) Cleanup completed!"

docker-clean: ## Clean up Docker resources
	@echo "$(BLUE)[INFO]$(NC) Cleaning up Docker resources..."
	@docker stop $(CONTAINER_NAME) 2>/dev/null || true
	@docker rm $(CONTAINER_NAME) 2>/dev/null || true
	@docker rmi $(IMAGE_NAME) 2>/dev/null || true
	@docker system prune -f
	@echo "$(GREEN)[SUCCESS]$(NC) Docker cleanup completed!"

clean-all: clean docker-clean ## Clean up everything

# Development workflow commands
dev-setup: setup install ## Complete development setup
dev-test: test lint security-scan ## Run all development tests
dev-run: run-dev ## Run in development mode

# Production commands
prod-build: docker-build ## Build for production
prod-run: compose-up ## Run in production mode
prod-stop: compose-down ## Stop production services

# Quick commands
quick-start: setup docker-build docker-run ## Quick start (setup, build, run)
quick-stop: docker-stop docker-clean ## Quick stop and cleanup
quick-test: test ## Quick test run

# Show version
version: ## Show version information
	@echo "$(BLUE)[INFO]$(NC) Kali MCP Server Version Information"
	@echo "=============================================="
	@echo "Version: 1.0.0"
	@echo "Python: $$($(PYTHON) --version)"
	@echo "Docker: $$(docker --version 2>/dev/null || echo 'Not installed')"
	@echo "Docker Compose: $$(docker-compose --version 2>/dev/null || echo 'Not installed')"
