#!/bin/bash

# Скрипт для запуска тестов в контейнерах
# Автоматически очищает тестовую БД после завершения

set -e

echo "Запуск тестов в контейнерах..."

# Останавливаем и удаляем существующие тестовые контейнеры
echo "Очистка предыдущих тестовых контейнеров..."
docker compose -f infra/docker-compose.test.yaml down -v --remove-orphans 2>/dev/null || true

# Запускаем тесты
echo "Запуск тестовых контейнеров..."
docker compose -f infra/docker-compose.test.yaml up --build --abort-on-container-exit

# Получаем код выхода из тестового контейнера (до его остановки)
TEST_EXIT_CODE=$(docker compose -f infra/docker-compose.test.yaml ps -q backend-test | head -1 | xargs docker inspect -f '{{.State.ExitCode}}' 2>/dev/null || echo "0")

# Останавливаем и удаляем контейнеры
echo "Очистка тестовых контейнеров..."
docker compose -f infra/docker-compose.test.yaml down -v --remove-orphans

# Удаляем тестовые образы
echo "Удаление тестовых образов..."
docker rmi inventory-test-backend-test 2>/dev/null || true
docker rmi inventory-test-postgresdb-test 2>/dev/null || true

# Выводим результат
if [ "$TEST_EXIT_CODE" -eq 0 ]; then
    echo "Тесты прошли успешно!"
    exit 0
else
    echo "Тесты завершились с ошибкой (код: $TEST_EXIT_CODE)"
    exit $TEST_EXIT_CODE
fi 