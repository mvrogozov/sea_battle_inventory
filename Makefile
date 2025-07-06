.PHONY: help test test-local test-container clean clean-test clean-all build run stop

# Переменные
DOCKER_COMPOSE = docker-compose -f infra/docker-compose.yaml
DOCKER_COMPOSE_TEST = docker-compose -f infra/docker-compose.test.yaml

help: ## Показать справку
	@echo "Доступные команды:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

test: ## Запустить тесты (локально с SQLite)
	@echo "Проверка прав доступа к файлам логов..."
	@if [ -f "app/logs/main.log" ] && [ ! -w "app/logs/main.log" ]; then \
		echo "Исправление прав доступа к main.log..."; \
		sudo chown $(USER):$(USER) app/logs/main.log 2>/dev/null || true; \
	fi
	@chmod +x scripts/run_tests_local.sh
	@./scripts/run_tests_local.sh

test-local: test ## Алиас для локальных тестов

test-container: ## Запустить тесты в контейнерах с PostgreSQL
	@chmod +x scripts/run_tests.sh
	@./scripts/run_tests.sh

test-coverage: ## Запустить тесты с покрытием кода
	@echo "Запуск тестов с покрытием..."
	@bash -c "source venv/bin/activate && pytest --cov=app --cov-report=html --cov-report=term-missing -v"

build: ## Собрать контейнеры
	@echo "Сборка контейнеров..."
	@$(DOCKER_COMPOSE) build

run: ## Запустить приложение
	@echo "Запуск приложения..."
	@$(DOCKER_COMPOSE) up -d

stop: ## Остановить приложение
	@echo "Остановка приложения..."
	@$(DOCKER_COMPOSE) down

clean: ## Очистить контейнеры и образы
	@echo "Очистка контейнеров и образов..."
	@$(DOCKER_COMPOSE) down -v --remove-orphans
	@docker system prune -f

clean-test: ## Очистить тестовые контейнеры
	@echo "Очистка тестовых контейнеров..."
	@$(DOCKER_COMPOSE_TEST) down -v --remove-orphans
	@docker rmi inventory-test-backend-test 2>/dev/null || true
	@docker rmi inventory-test-postgresdb-test 2>/dev/null || true

clean-all: clean clean-test ## Полная очистка
	@echo "Полная очистка..."
	@rm -f test.db
	@rm -rf htmlcov/
	@rm -rf .pytest_cache/
	@rm -rf __pycache__/
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

logs: ## Показать логи приложения
	@$(DOCKER_COMPOSE) logs -f

logs-test: ## Показать логи тестов
	@$(DOCKER_COMPOSE_TEST) logs -f

status: ## Показать статус контейнеров
	@echo "📊 Статус контейнеров приложения:"
	@$(DOCKER_COMPOSE) ps
	@echo ""
	@echo "📊 Статус тестовых контейнеров:"
	@$(DOCKER_COMPOSE_TEST) ps 