import logging
from typing import AsyncGenerator

from sqlalchemy.exc import SQLAlchemyError
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, async_sessionmaker
from sqlmodel import SQLModel
from sqlalchemy import text

from app.config import settings

logger = logging.getLogger(__name__)

engine: AsyncEngine = create_async_engine(settings.db_url)

async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Асинхронный генератор сессий для работы с базой данных.
    Используется для получения сессии в эндпоинтах и репозиториях.
    Пример использования:
        async with get_session() as session:
            ...
    """
    async with async_session_maker() as session:
        yield session


async def create_db_and_tables():
    """
    Асинхронно создаёт все таблицы в базе данных согласно моделям SQLModel.
    Используется при инициализации приложения.
    """
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def check_connection() -> bool:
    """
    Проверяет соединение с базой данных.
    Возвращает True, если соединение успешно, иначе False.
    """
    try:
        async with engine.connect() as conn:
            await conn.execute(text('SELECT 1'))
        logger.info('Database test connection successful')
        return True
    except SQLAlchemyError as e:
        logger.error(f'Database connection failed: {e}')
        return False


async def init_db() -> None:
    """
    Инициализирует базу данных: проверяет соединение и создаёт таблицы, если соединение успешно.
    """
    if await check_connection():
        await create_db_and_tables()
