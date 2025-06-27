import os

from pydantic_settings import BaseSettings
from pydantic import PostgresDsn, Field


class Settings(BaseSettings):

    LOG_PATH: str = 'app/logs'
    db_host: str = Field(alias="DB_HOST")
    db_user: str = Field(alias="POSTGRES_USER")
    db_password: str = Field(alias="POSTGRES_PASSWORD")
    db_name: str = Field(alias="POSTGRES_DB")
    db_port: int = Field(alias="DB_PORT", default=5432)

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
