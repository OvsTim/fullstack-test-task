from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.core.config import settings

engine: AsyncEngine = create_async_engine(settings.database_url)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)

sync_engine = create_engine(settings.database_url_sync)
sync_session_maker = sessionmaker(sync_engine, expire_on_commit=False)


async def dispose_engine() -> None:
    await engine.dispose()
    sync_engine.dispose()
