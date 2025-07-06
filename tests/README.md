# Тестирование проекта Sea Battle Inventory

## Обзор

В проекте реализована система тестирования для FastAPI приложения управления инвентарём игры "Морской бой".

## Запуск тестов

### Основные команды (Makefile)

```bash
# Локальные тесты (SQLite)
make test

# Тесты в контейнерах (PostgreSQL)
make test-container

# Тесты с покрытием кода
make test-coverage

# Очистка тестовых контейнеров
make clean-test
```

## Структура тестов

```
tests/
├── __init__.py
├── conftest.py              # Конфигурация pytest и фикстуры
├── test_items_api.py        # Тесты API эндпоинтов предметов
├── test_inventory_api.py    # Тесты API эндпоинтов инвентаря
├── test_services.py         # Тесты сервисного слоя
├── test_auth.py             # Тесты аутентификации и авторизации
└── README.md                # Эта документация
```

## Особенности
- Асинхронные тесты через `pytest-asyncio`
- Все внешние сервисы и кэш замокированы
- Инициализация БД замокирована через фикстуру
- Автоматическая очистка тестовой БД
- Поддержка SQLite (локально) и PostgreSQL (в контейнерах)

## Управление контейнерами

```bash
make build          # Собрать контейнеры
make run            # Запустить приложение
make stop           # Остановить приложение
make logs           # Показать логи
make clean          # Очистить контейнеры приложения
make clean-test     # Очистить тестовые контейнеры
make clean-all      # Полная очистка
```
бф
## Пример теста

```python
async def test_get_item_success(self, item_service, mock_item):
    item_service.item_repo.get_item = AsyncMock(return_value=mock_item)
    result = await item_service.get_item(1)
    assert result.id == 1
    assert result.name == "Test Item"
```

## Покрытие кода

- Запуск покрытия: `make test-coverage`
- HTML-отчёт: `htmlcov/index.html` (откройте в браузере после запуска)
- Текущее покрытие: ~64% (769 строк кода, 279 непокрытых)
- Целевой порог покрытия: 80% (настроен в pytest.ini)

### Покрываемые модули:
- **API эндпоинты** (96-100% покрытия)
  - `app/api/items.py` - управление предметами
  - `app/api/inventory.py` - управление инвентарём
  - `app/api/responses.py` - HTTP-ответы
- **Сервисный слой** (65-75% покрытия)
  - `app/services/item_service.py` - бизнес-логика предметов
  - `app/services/inventory_service.py` - бизнес-логика инвентаря
- **Аутентификация и авторизация** (100% покрытия)
  - Проверка JWT токенов и ролей (логика реализована в сервисах и утилитах, тесты — в `tests/test_auth.py`)
- **Модели и схемы** (95-100% покрытия)
  - `app/inventory/models.py` - модели данных
  - `app/inventory/schemas.py` - Pydantic схемы
- **Конфигурация и исключения** (100% покрытия)
  - `app/config.py` - настройки приложения
  - `app/exceptions.py` - пользовательские исключения

### Модули с низким покрытием:
- `app/base.py` (24%) - базовые классы и утилиты
- `app/database.py` (55%) - подключение к БД
- `app/repositories/` (20-48%) - слой доступа к данным
- `app/item_script/` (80%) - скрипт предметов

**Примечание**: Репозитории и база данных замокированы в тестах, поэтому их низкое покрытие не критично для функциональности.
