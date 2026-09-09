from pathlib import Path
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from enterprise_ai.ingestion.service import DocumentIngestionService
from enterprise_ai.persistence.models.document import Document, DocumentStatus
from enterprise_ai.storage.local import LocalFileStorage


@pytest.mark.anyio
async def test_extract_document_text_marks_document_completed(
    tmp_path: Path,
) -> None:
    storage = LocalFileStorage(root_directory=tmp_path)

    stored_file = tmp_path / "document.txt"
    stored_file.write_text(
        "Hello     Enterprise AI\n\n\nFastAPI",
        encoding="utf-8",
    )

    document = Document(
        id=uuid4(),
        name="document.txt",
        source_type="upload",
        storage_path="document.txt",
        knowledge_base_id=uuid4(),
        organization_id=uuid4(),
        status=DocumentStatus.PENDING,
    )

    session = AsyncMock()

    service = DocumentIngestionService()

    text = await service.extract_document_text(
        document=document,
        storage=storage,
        session=session,
    )

    assert text == "Hello Enterprise AI\n\nFastAPI"
    assert document.status == DocumentStatus.COMPLETED
    assert document.error_message is None

    assert session.commit.await_count == 2
    assert session.refresh.await_count == 2


@pytest.mark.anyio
async def test_extract_document_text_marks_document_failed(
    tmp_path: Path,
) -> None:
    storage = LocalFileStorage(root_directory=tmp_path)

    stored_file = tmp_path / "document.docx"
    stored_file.write_text(
        "unsupported content",
        encoding="utf-8",
    )

    document = Document(
        id=uuid4(),
        name="document.docx",
        source_type="upload",
        storage_path="document.docx",
        knowledge_base_id=uuid4(),
        organization_id=uuid4(),
        status=DocumentStatus.PENDING,
    )

    session = AsyncMock()

    service = DocumentIngestionService()

    with pytest.raises(ValueError, match="Unsupported file type"):
        await service.extract_document_text(
            document=document,
            storage=storage,
            session=session,
        )

    assert document.status == DocumentStatus.FAILED
    assert document.error_message == "Unsupported file type: .docx"

    assert session.commit.await_count == 2
    assert session.refresh.await_count == 2


@pytest.mark.anyio
async def test_extract_document_text_requires_uploaded_file() -> None:
    document = Document(
        id=uuid4(),
        name="document.txt",
        source_type="upload",
        storage_path=None,
        knowledge_base_id=uuid4(),
        organization_id=uuid4(),
        status=DocumentStatus.PENDING,
    )

    storage = LocalFileStorage(root_directory=Path("unused"))
    session = AsyncMock()

    service = DocumentIngestionService()

    with pytest.raises(
        ValueError,
        match="Document has no uploaded file",
    ):
        await service.extract_document_text(
            document=document,
            storage=storage,
            session=session,
        )

    assert document.status == DocumentStatus.PENDING
    session.commit.assert_not_awaited()
    session.refresh.assert_not_awaited()


@pytest.mark.anyio
async def test_extract_document_text_marks_empty_document_failed(
    tmp_path: Path,
) -> None:
    storage = LocalFileStorage(root_directory=tmp_path)

    stored_file = tmp_path / "empty.txt"
    stored_file.write_text(
        "   \n\n\t   ",
        encoding="utf-8",
    )

    document = Document(
        id=uuid4(),
        name="empty.txt",
        source_type="upload",
        storage_path="empty.txt",
        knowledge_base_id=uuid4(),
        organization_id=uuid4(),
        status=DocumentStatus.PENDING,
    )

    session = AsyncMock()
    service = DocumentIngestionService()

    with pytest.raises(
        ValueError,
        match="Document contains no extractable text",
    ):
        await service.extract_document_text(
            document=document,
            storage=storage,
            session=session,
        )

    assert document.status == DocumentStatus.FAILED
    assert document.error_message == "Document contains no extractable text"

    assert session.commit.await_count == 2
    assert session.refresh.await_count == 2
