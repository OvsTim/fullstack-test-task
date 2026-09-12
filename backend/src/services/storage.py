from pathlib import Path
from typing import BinaryIO


class LocalStorage:
    def __init__(self, root: Path) -> None:
        self._root = root

    def _path(self, stored_name: str) -> Path:
        return self._root / stored_name

    def save(self, stored_name: str, data: bytes) -> None:
        self._path(stored_name).write_bytes(data)

    def open(self, stored_name: str) -> BinaryIO:
        return self._path(stored_name).open("rb")

    def delete(self, stored_name: str) -> None:
        path = self._path(stored_name)
        if path.exists():
            path.unlink()

    def exists(self, stored_name: str) -> bool:
        return self._path(stored_name).exists()
