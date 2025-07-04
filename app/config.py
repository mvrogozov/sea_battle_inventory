import os

from pydantic import Field, PostgresDsn
from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    LOG_PATH: str = 'app/logs'
    db_host: str = Field(alias='DB_HOST')
    db_user: str = Field(alias='POSTGRES_USER')
    db_password: str = Field(alias='POSTGRES_PASSWORD')
    db_name: str = Field(alias='POSTGRES_DB')
    db_port: int = Field(alias='DB_PORT', default=5432)
    KAFKA_SERVER: str = Field(alias='KAFKA_SERVER')
    REDIS_HOST: str = Field(alias='REDIS_HOST')
    REDIS_PORT: int = Field(alias='REDIS_PORT', default=6379)
    CACHE_EXPIRE: int = 3600  # seconds

    @property
    def db_url(self) -> PostgresDsn:
        return (
            f'postgresql+asyncpg://{self.db_user}:{self.db_password}@'
            f'{self.db_host}:{self.db_port}/{self.db_name}'
        )

    class Config:
        env_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            '..', 'infra', '.env'
        )
        extra = 'ignore'


settings = Settings()
os.makedirs(settings.LOG_PATH, exist_ok=True)
