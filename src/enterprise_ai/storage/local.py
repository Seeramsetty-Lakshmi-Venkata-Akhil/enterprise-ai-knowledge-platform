from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from shutil import copyfile

from enterprise_ai.storage.base import StorageService


class LocalFileStorage(StorageService):
    def __init__(self, root_directory: Path) -> None:
        self.root_directory = root_directory

    async def save(
        self,
        *,
        source_path: Path,
        destination_path: str,
    ) -> str:
        target_path = self.root_directory / destination_path
        target_path.parent.mkdir(parents=True, exist_ok=True)

        copyfile(source_path, target_path)

        return destination_path

    @asynccontextmanager
    async def open_for_read(
        self,
        *,
        storage_path: str,
    ) -> AsyncIterator[Path]:
        file_path = self.root_directory / storage_path

        if not file_path.is_file():
            raise FileNotFoundError(f"Stored file not found: {storage_path}")

        yield file_path
