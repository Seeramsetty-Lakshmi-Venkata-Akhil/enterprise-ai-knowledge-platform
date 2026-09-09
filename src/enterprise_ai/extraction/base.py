from abc import ABC, abstractmethod
from pathlib import Path


class TextExtractor(ABC):
    @abstractmethod
    async def extract(self, file_path: Path) -> str:
        """Extract raw text from a file."""
        raise NotImplementedError
