from pathlib import Path

import pymupdf

from enterprise_ai.extraction.base import TextExtractor


class PDFTextExtractor(TextExtractor):
    async def extract(self, file_path: Path) -> str:
        document = pymupdf.open(file_path)

        try:
            pages: list[str] = []

            for page in document:
                page_text = page.get_text()
                pages.append(page_text)

            return "\n".join(pages)
        finally:
            document.close()
