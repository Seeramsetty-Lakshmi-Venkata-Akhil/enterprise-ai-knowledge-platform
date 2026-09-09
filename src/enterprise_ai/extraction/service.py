from pathlib import Path

from enterprise_ai.extraction.base import TextExtractor
from enterprise_ai.extraction.normalization import normalize_text


class TextExtractionService:
    async def extract_and_normalize(
        self,
        *,
        extractor: TextExtractor,
        file_path: Path,
    ) -> str:
        raw_text = await extractor.extract(file_path)
        normalized_text = normalize_text(raw_text)

        if not normalized_text:
            raise ValueError("Document contains no extractable text")

        return normalized_text
