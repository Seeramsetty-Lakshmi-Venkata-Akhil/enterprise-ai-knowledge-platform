from abc import ABC, abstractmethod
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
