from pathlib import Path

from enterprise_ai.extraction.base import TextExtractor
from enterprise_ai.extraction.pdf import PDFTextExtractor
from enterprise_ai.extraction.text import PlainTextExtractor


def get_text_extractor(file_path: Path) -> TextExtractor:
    suffix = file_path.suffix.lower()

    if suffix == ".pdf":
        return PDFTextExtractor()

    if suffix == ".txt":
        return PlainTextExtractor()

    raise ValueError(f"Unsupported file type: {suffix}")
