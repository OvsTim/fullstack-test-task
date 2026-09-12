import mimetypes
from collections.abc import AsyncIterator, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Protocol
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.enums import ProcessingStatus
from src.core.exceptions import EmptyFile, FileNotFound, StoredFileMissing
from src.db.models import StoredFile
from src.repositories.files import FileRepository
from src.services.storage import LocalStorage

_CHUNK_SIZE = 64 * 1024


class AsyncByteReader(Protocol):
    async def read(self, size: int = -1) -> bytes: ...


@dataclass(slots=True)
class FileDownload:
    stream: BinaryIO
    mime_type: str
    filename: str

    def iter_chunks(self, chunk_size: int = _CHUNK_SIZE) -> Iterator[bytes]:
        try:
            while True:
                chunk = self.stream.read(chunk_size)
                if not chunk:
                    break
                yield chunk
        finally:
            self.stream.close()


class FileService:
    def __init__(
        self,
        session: AsyncSession,
        files: FileRepository,
        storage: LocalStorage,
    ) -> None:
        self._session = session
        self._files = files
        self._storage = storage

    async def list(self) -> list[StoredFile]:
        return await self._files.list()

    async def get(self, file_id: str) -> StoredFile:
        file_item = await self._files.get(file_id)
        if file_item is None:
            raise FileNotFound
        return file_item

    async def upload(
        self,
        title: str,
        filename: str | None,
        content_type: str | None,
        stream: AsyncByteReader,
    ) -> StoredFile:
        file_id = str(uuid4())
        suffix = Path(filename or "").suffix
        stored_name = f"{file_id}{suffix}"
        size = await self._storage.save_stream(stored_name, _iter_chunks(stream))
        if size == 0:
            raise EmptyFile

        file_item = StoredFile(
            id=file_id,
            title=title,
            original_name=filename or stored_name,
            stored_name=stored_name,
            mime_type=content_type or mimetypes.guess_type(stored_name)[0] or "application/octet-stream",
            size=size,
            processing_status=ProcessingStatus.UPLOADED.value,
        )
        self._files.add(file_item)
        await self._session.commit()
        await self._session.refresh(file_item)
        return file_item

    async def update(self, file_id: str, title: str) -> StoredFile:
        file_item = await self.get(file_id)
        file_item.title = title
        await self._session.commit()
        await self._session.refresh(file_item)
        return file_item

    async def delete(self, file_id: str) -> None:
        file_item = await self.get(file_id)
        self._storage.delete(file_item.stored_name)
        await self._files.delete(file_item)
        await self._session.commit()

    async def download(self, file_id: str) -> FileDownload:
        file_item = await self.get(file_id)
        if not self._storage.exists(file_item.stored_name):
            raise StoredFileMissing
        return FileDownload(
            stream=self._storage.open(file_item.stored_name),
            mime_type=file_item.mime_type,
            filename=file_item.original_name,
        )


async def _iter_chunks(stream: AsyncByteReader, chunk_size: int = _CHUNK_SIZE) -> AsyncIterator[bytes]:
    while True:
        chunk = await stream.read(chunk_size)
        if not chunk:
            break
        yield chunk
