import os

os.environ["POSTGRES_DB"] = "pytest"
os.environ.setdefault("POSTGRES_USER", "postgres")
os.environ.setdefault("POSTGRES_PASSWORD", "postgres")
os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("PGPORT", "5434")
os.environ.setdefault("CELERY_BROKER_URL", "redis://localhost:6379/0")

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from src.core.config import settings
from src.db.models import Base
from src.db.session import engine


def _admin_url() -> str:
    return (
        f"postgresql+asyncpg://{settings.postgres_user}:{settings.postgres_password}"
        f"@{settings.postgres_host}:{settings.pgport}/postgres"
    )


async def _prepare_database() -> None:
    admin = create_async_engine(_admin_url(), isolation_level="AUTOCOMMIT")
    async with admin.connect() as conn:
        exists = await conn.scalar(text("SELECT 1 FROM pg_database WHERE datname = 'pytest'"))
        if not exists:
            await conn.execute(text("CREATE DATABASE pytest"))
    await admin.dispose()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


async def _dispose_engine() -> None:
    await engine.dispose()


@pytest.fixture(scope="session", autouse=True)
async def setup_database() -> None:
    await _prepare_database()
    yield
    await _dispose_engine()


@pytest.fixture
async def client(tmp_path, monkeypatch):
    storage = tmp_path / "files"
    storage.mkdir()
    monkeypatch.setattr(settings, "storage_dir", storage)
    monkeypatch.setattr("src.api.routers.files.scan_file_for_threats.delay", lambda *args, **kwargs: None)
    monkeypatch.setattr("src.workers.tasks.extract_file_metadata.delay", lambda *args, **kwargs: None)

    async with engine.begin() as conn:
        await conn.execute(text("TRUNCATE alerts, files RESTART IDENTITY CASCADE"))

    from src.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as async_client:
        yield async_client
