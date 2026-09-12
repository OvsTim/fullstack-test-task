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

from src.models import Base
from src.service import engine as service_engine
from src.tasks import engine as tasks_engine


def _admin_url() -> str:
    user = os.environ["POSTGRES_USER"]
    password = os.environ["POSTGRES_PASSWORD"]
    host = os.environ["POSTGRES_HOST"]
    port = os.environ["PGPORT"]
    return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/postgres"


async def _prepare_database() -> None:
    admin = create_async_engine(_admin_url(), isolation_level="AUTOCOMMIT")
    async with admin.connect() as conn:
        exists = await conn.scalar(text("SELECT 1 FROM pg_database WHERE datname = 'pytest'"))
        if not exists:
            await conn.execute(text("CREATE DATABASE pytest"))
    await admin.dispose()

    async with service_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def _dispose_engines() -> None:
    await service_engine.dispose()
    await tasks_engine.dispose()


@pytest.fixture(scope="session", autouse=True)
async def setup_database() -> None:
    await _prepare_database()
    yield
    await _dispose_engines()


@pytest.fixture
async def client(tmp_path, monkeypatch):
    storage = tmp_path / "files"
    storage.mkdir()
    monkeypatch.setattr("src.service.STORAGE_DIR", storage)
    monkeypatch.setattr("src.app.STORAGE_DIR", storage)
    monkeypatch.setattr("src.tasks.STORAGE_DIR", storage)
    monkeypatch.setattr("src.app.scan_file_for_threats.delay", lambda *args, **kwargs: None)
    monkeypatch.setattr("src.tasks.extract_file_metadata.delay", lambda *args, **kwargs: None)

    async with service_engine.begin() as conn:
        await conn.execute(text("TRUNCATE alerts, files RESTART IDENTITY CASCADE"))

    from src.app import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as async_client:
        yield async_client
