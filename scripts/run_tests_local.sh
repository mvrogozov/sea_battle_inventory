#!/bin/bash

# Скрипт для запуска тестов локально с SQLite
# Автоматически очищает тестовую БД после завершения

set -e

echo "Запуск тестов локально..."

# Проверяем наличие виртуального окружения
if [ ! -d "venv" ]; then
    echo "Создание виртуального окружения..."
    python3 -m venv venv
fi

# Активируем виртуальное окружение
echo "Активация виртуального окружения..."
source venv/bin/activate

# Устанавливаем зависимости
echo "Установка зависимостей..."
pip install -r requirements/requirements.txt
pip install -r requirements/test-requirements.txt

# Исправляем права доступа к файлам логов (если они принадлежат root)
echo "Проверка прав доступа к файлам логов..."
if [ -f "app/logs/main.log" ] && [ ! -w "app/logs/main.log" ]; then
    echo "Исправление прав доступа к main.log..."
    sudo chown $USER:$USER app/logs/main.log 2>/dev/null || true
fi

# Удаляем старую тестовую БД если она существует
echo "Очистка старой тестовой БД..."
rm -f test.db

# Запускаем тесты
echo "Запуск тестов..."
pytest --maxfail=10 --disable-warnings -v

# Очищаем тестовую БД после тестов
echo "Очистка тестовой БД..."
rm -f test.db

echo "Тесты завершены!"