from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import StoredFile


class FileRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, file_id: str) -> StoredFile | None:
        return await self._session.get(StoredFile, file_id)

    async def list(self) -> list[StoredFile]:
        result = await self._session.execute(select(StoredFile).order_by(StoredFile.created_at.desc()))
        return list(result.scalars().all())

    def add(self, file_item: StoredFile) -> None:
        self._session.add(file_item)

    async def delete(self, file_item: StoredFile) -> None:
        await self._session.delete(file_item)
