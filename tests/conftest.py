import asyncio
import os
import pytest
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import get_session
from app.inventory.schemas import UserInfo
from app.services.item_service import get_item_service, ItemService
from app.services.inventory_service import InventoryService, get_inventory_service


# Определяем URL тестовой БД
def get_test_database_url():
    """Получает URL тестовой БД из переменных окружения или использует SQLite по умолчанию"""
    if os.getenv("TESTING") == "true" and os.getenv("DATABASE_URL"):
        # Используем PostgreSQL для тестов в контейнере
        return os.getenv("DATABASE_URL")
    else:
        # Используем SQLite для локальных тестов
        return "sqlite+aiosqlite:///./test.db"


SQLALCHEMY_DATABASE_URL = get_test_database_url()

# Создаём движок в зависимости от типа БД
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    engine = create_async_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
    # PostgreSQL
    engine = create_async_engine(
        SQLALCHEMY_DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
    )

TestingSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        yield session


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
async def setup_database():
    """Создание и очистка тестовой БД"""
    # Создаём таблицы
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    
    yield
    
    # Очищаем БД после тестов
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
    
    # Закрываем соединения
    await engine.dispose()


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Фикстура для тестовой сессии БД"""
    async with TestingSessionLocal() as session:
        yield session


@pytest.fixture
def mock_cache():
    """Фикстура для мок-кэша"""
    mock_cache = AsyncMock()
    mock_cache.get.return_value = None
    mock_cache.set.return_value = None
    mock_cache.delete.return_value = None
    mock_cache.flush.return_value = None
    return mock_cache


@pytest.fixture
def patch_fastapi_cache():
    with patch('fastapi_cache.caches.set'), patch('fastapi_cache.caches.get'):
        yield


@pytest.fixture
def client(mock_cache, patch_fastapi_cache) -> Generator:
    """Фикстура для тестового клиента"""
    # Мокируем кэш для предотвращения ошибки регистрации
    with patch('app.inventory.common.get_cache', return_value=mock_cache):
        app.dependency_overrides[get_session] = override_get_session
        with TestClient(app) as test_client:
            yield test_client
        app.dependency_overrides.clear()


@pytest.fixture
def mock_user() -> UserInfo:
    """Фикстура для тестового пользователя"""
    return UserInfo(user_id=1, role="user")


@pytest.fixture
def mock_admin() -> UserInfo:
    """Фикстура для тестового администратора"""
    return UserInfo(user_id=1, role="admin")


@pytest.fixture
def mock_jwt_token() -> str:
    """Фикстура для тестового JWT токена"""
    return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJyb2xlIjoidXNlciIsImV4cCI6MTc1MTQwODU5MX0.test_signature"


@pytest.fixture
def mock_admin_jwt_token() -> str:
    """Фикстура для тестового JWT токена администратора"""
    return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJyb2xlIjoiYWRtaW4iLCJleHAiOjE3NTE0MDg1OTF9.test_signature"


@pytest.fixture
def mock_item_service(mock_cache):
    """Фикстура для мок-сервиса предметов"""
    mock_service = AsyncMock(spec=ItemService)
    mock_service.cache = mock_cache
    app.dependency_overrides[get_item_service] = lambda: mock_service
    yield mock_service
    app.dependency_overrides.pop(get_item_service, None)


@pytest.fixture
def mock_inventory_service(mock_cache, mock_item_service):
    """Фикстура для мок-сервиса инвентаря"""
    mock_service = AsyncMock(spec=InventoryService)
    mock_service.cache = mock_cache
    mock_service.item_service = mock_item_service
    app.dependency_overrides[get_inventory_service] = lambda: mock_service
    yield mock_service
    app.dependency_overrides.pop(get_inventory_service, None)


@pytest.fixture(autouse=True)
def patch_init_db():
    """Мокает init_db в app.main, чтобы не запускалась реальная инициализация БД при тестах"""
    with patch("app.main.init_db", new=AsyncMock()):
        yield


@pytest.fixture(autouse=True)
def patch_redis_init():
    """Мокает инициализацию Redis в app.main, чтобы избежать ошибок подключения"""
    with patch("app.main.RedisCacheBackend") as mock_redis:
        # Создаём мок для Redis кэша
        mock_redis_instance = AsyncMock()
        mock_redis_instance.set.return_value = None
        mock_redis_instance.get.return_value = "ok"
        mock_redis.return_value = mock_redis_instance
        
        # Мокаем caches.set
        with patch("app.main.caches.set") as mock_caches_set:
            yield 


@pytest.fixture(autouse=True)
def patch_kafka_producer():
    """Мокает KafkaProducer в app.main, чтобы не было реального подключения к Kafka в тестах"""
    with patch("app.main.AIOKafkaProducer") as mock_producer:
        mock_instance = AsyncMock()
        mock_instance.start.return_value = None
        mock_instance.stop.return_value = None
        mock_producer.return_value = mock_instance
        yield 


@pytest.fixture(autouse=True)
def patch_kafka_consumer():
    with patch("app.services.inventory_service.AIOKafkaConsumer") as mock_consumer:
        mock_instance = AsyncMock()
        mock_instance.start.return_value = None
        mock_instance.stop.return_value = None
        mock_consumer.return_value = mock_instance
        yield 