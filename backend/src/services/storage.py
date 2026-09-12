from collections.abc import AsyncIterable
from pathlib import Path
from typing import BinaryIO


class LocalStorage:
    def __init__(self, root: Path) -> None:
        self._root = root

    def _path(self, stored_name: str) -> Path:
        return self._root / stored_name

    async def save_stream(self, stored_name: str, chunks: AsyncIterable[bytes]) -> int:
        path = self._path(stored_name)
        size = 0
        try:
            with path.open("wb") as dest:
                async for chunk in chunks:
                    dest.write(chunk)
                    size += len(chunk)
        except Exception:
            path.unlink(missing_ok=True)
            raise
        if size == 0:
            path.unlink(missing_ok=True)
        return size

    def open(self, stored_name: str) -> BinaryIO:
        return self._path(stored_name).open("rb")

    def delete(self, stored_name: str) -> None:
        path = self._path(stored_name)
        if path.exists():
            path.unlink()

    def exists(self, stored_name: str) -> bool:
        return self._path(stored_name).exists()
