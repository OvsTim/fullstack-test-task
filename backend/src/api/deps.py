from collections.abc import AsyncIterator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.db.session import async_session_maker
from src.repositories.alerts import AlertRepository
from src.repositories.files import FileRepository
from src.services.alerting import AlertService
from src.services.file_service import FileService
from src.services.storage import LocalStorage


async def get_session() -> AsyncIterator[AsyncSession]:
    async with async_session_maker() as session:
        yield session


def get_file_service(session: AsyncSession = Depends(get_session)) -> FileService:
    return FileService(
        session=session,
        files=FileRepository(session),
        storage=LocalStorage(settings.storage_dir),
    )


def get_alert_service(session: AsyncSession = Depends(get_session)) -> AlertService:
    return AlertService(alerts=AlertRepository(session))
