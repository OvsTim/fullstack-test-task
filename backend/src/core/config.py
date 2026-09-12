from pathlib import Path

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    postgres_user: str
    postgres_password: str
    postgres_host: str
    pgport: int = 5432
    postgres_db: str
    celery_broker_url: str
    storage_dir: Path = _BACKEND_DIR / "storage" / "files"

    @computed_field
    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.pgport}/{self.postgres_db}"
        )

    @computed_field
    @property
    def database_url_sync(self) -> str:
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.pgport}/{self.postgres_db}"
        )


settings = Settings()
