from sqlalchemy.ext.asyncio import AsyncSession

from enterprise_ai.extraction.factory import get_text_extractor
from enterprise_ai.extraction.service import TextExtractionService
from enterprise_ai.persistence.models.document import Document, DocumentStatus
from enterprise_ai.storage.base import StorageService


class DocumentIngestionService:
    def __init__(self) -> None:
        self.text_extraction_service = TextExtractionService()

    async def extract_document_text(
        self,
        *,
        document: Document,
        storage: StorageService,
        session: AsyncSession,
    ) -> str:
        if document.storage_path is None:
            raise ValueError("Document has no uploaded file")

        document.status = DocumentStatus.PROCESSING
        document.error_message = None

        await session.commit()
        await session.refresh(document)

        try:
            async with storage.open_for_read(
                storage_path=document.storage_path,
            ) as file_path:
                extractor = get_text_extractor(file_path)

                text = await self.text_extraction_service.extract_and_normalize(
                    extractor=extractor,
                    file_path=file_path,
                )

            document.status = DocumentStatus.COMPLETED
            document.error_message = None

            await session.commit()
            await session.refresh(document)

            return text

        except Exception as exc:
            document.status = DocumentStatus.FAILED
            document.error_message = str(exc)

            await session.commit()
            await session.refresh(document)

            raise
