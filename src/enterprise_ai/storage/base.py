from abc import ABC, abstractmethod
from contextlib import AbstractAsyncContextManager
from pathlib import Path


class StorageService(ABC):
    @abstractmethod
    async def save(
        self,
        *,
        source_path: Path,
        destination_path: str,
    ) -> str:
        """Store a file and return its storage path."""
        raise NotImplementedError

    @abstractmethod
    def open_for_read(
        self,
        *,
        storage_path: str,
    ) -> AbstractAsyncContextManager[Path]:
        """Provide temporary/local readable access to a stored file."""
        raise NotImplementedError
