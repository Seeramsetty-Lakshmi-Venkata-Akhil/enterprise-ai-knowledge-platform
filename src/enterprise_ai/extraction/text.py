from pathlib import Path

from enterprise_ai.extraction.base import TextExtractor


class PlainTextExtractor(TextExtractor):
    async def extract(self, file_path: Path) -> str:
        return file_path.read_text(encoding="utf-8")
