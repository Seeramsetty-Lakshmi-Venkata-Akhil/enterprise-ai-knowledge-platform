from pathlib import Path

from enterprise_ai.core.config import get_settings
from enterprise_ai.storage.base import StorageService
from enterprise_ai.storage.local import LocalFileStorage


def get_storage_service() -> StorageService:
    settings = get_settings()

    return LocalFileStorage(
        root_directory=Path(settings.storage_root),
    )
