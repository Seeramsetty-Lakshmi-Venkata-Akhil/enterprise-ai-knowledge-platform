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

        target_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        copyfile(
            source_path,
            target_path,
        )

        return destination_path
