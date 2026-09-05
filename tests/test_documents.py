from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

from fastapi.testclient import TestClient

from enterprise_ai.api.dependencies import get_current_user
from enterprise_ai.main import app
from enterprise_ai.persistence.database import get_db_session
from enterprise_ai.persistence.models.document import Document, DocumentStatus
from enterprise_ai.persistence.models.knowledge_base import KnowledgeBase
from enterprise_ai.persistence.models.user import User

ORGANIZATION_ID = UUID("11111111-1111-1111-1111-111111111111")
OTHER_ORGANIZATION_ID = UUID("22222222-2222-2222-2222-222222222222")

KNOWLEDGE_BASE_ID = UUID("33333333-3333-3333-3333-333333333333")
OTHER_KNOWLEDGE_BASE_ID = UUID("44444444-4444-4444-4444-444444444444")

DOCUMENT_ID = UUID("55555555-5555-5555-5555-555555555555")
OTHER_DOCUMENT_ID = UUID("66666666-6666-6666-6666-666666666666")

USER_ID = UUID("77777777-7777-7777-7777-777777777777")

NOW = datetime.now(UTC)


def build_current_user() -> User:
    return User(
        id=USER_ID,
        name="Akhil",
        email="akhil@example.com",
        password_hash="hashed-password",
        organization_id=ORGANIZATION_ID,
        created_at=NOW,
        updated_at=NOW,
    )


def build_knowledge_base(
    *,
    knowledge_base_id: UUID = KNOWLEDGE_BASE_ID,
    organization_id: UUID = ORGANIZATION_ID,
) -> KnowledgeBase:
    return KnowledgeBase(
        id=knowledge_base_id,
        name="Enterprise AI Knowledge Base",
        description="AI engineering documents",
        organization_id=organization_id,
        created_at=NOW,
        updated_at=NOW,
    )


def build_document(
    *,
    document_id: UUID = DOCUMENT_ID,
    knowledge_base_id: UUID = KNOWLEDGE_BASE_ID,
    organization_id: UUID = ORGANIZATION_ID,
    name: str = "architecture.pdf",
) -> Document:
    return Document(
        id=document_id,
        name=name,
        source_type="upload",
        storage_path="documents/architecture.pdf",
        status=DocumentStatus.PENDING,
        error_message=None,
        knowledge_base_id=knowledge_base_id,
        organization_id=organization_id,
        created_at=NOW,
        updated_at=NOW,
    )


def override_dependencies(
    session: AsyncMock,
    current_user: User,
) -> None:
    async def override_get_db_session():
        yield session

    async def override_get_current_user():
        return current_user

    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_current_user] = override_get_current_user


def clear_overrides() -> None:
    app.dependency_overrides.clear()


def test_create_document_uses_current_user_organization() -> None:
    session = AsyncMock()
    session.add = MagicMock()

    current_user = build_current_user()
    knowledge_base = build_knowledge_base()

    session.get.return_value = knowledge_base

    async def refresh_document(document: Document) -> None:
        document.id = DOCUMENT_ID
        document.status = DocumentStatus.PENDING
        document.created_at = NOW
        document.updated_at = NOW

    session.refresh.side_effect = refresh_document

    override_dependencies(session, current_user)

    try:
        with TestClient(app) as client:
            response = client.post(
                f"/knowledge-bases/{KNOWLEDGE_BASE_ID}/documents",
                json={
                    "name": "architecture.pdf",
                    "source_type": "upload",
                    "storage_path": "documents/architecture.pdf",
                },
            )

        assert response.status_code == 201

        body = response.json()

        assert body["id"] == str(DOCUMENT_ID)
        assert body["name"] == "architecture.pdf"
        assert body["source_type"] == "upload"
        assert body["status"] == "pending"
        assert body["knowledge_base_id"] == str(KNOWLEDGE_BASE_ID)
        assert body["organization_id"] == str(ORGANIZATION_ID)

        added_document = session.add.call_args.args[0]

        assert isinstance(added_document, Document)
        assert added_document.name == "architecture.pdf"
        assert added_document.source_type == "upload"
        assert added_document.knowledge_base_id == KNOWLEDGE_BASE_ID
        assert added_document.organization_id == ORGANIZATION_ID

        session.commit.assert_awaited_once()
        session.refresh.assert_awaited_once_with(added_document)

    finally:
        clear_overrides()


def test_create_document_returns_404_for_different_tenant_knowledge_base() -> None:
    session = AsyncMock()
    session.add = MagicMock()

    current_user = build_current_user()

    knowledge_base = build_knowledge_base(
        knowledge_base_id=OTHER_KNOWLEDGE_BASE_ID,
        organization_id=OTHER_ORGANIZATION_ID,
    )

    session.get.return_value = knowledge_base

    override_dependencies(session, current_user)

    try:
        with TestClient(app) as client:
            response = client.post(
                f"/knowledge-bases/{OTHER_KNOWLEDGE_BASE_ID}/documents",
                json={
                    "name": "secret.pdf",
                    "source_type": "upload",
                },
            )

        assert response.status_code == 404
        assert response.json() == {
            "detail": "Knowledge base not found",
        }

        session.add.assert_not_called()
        session.commit.assert_not_awaited()

    finally:
        clear_overrides()


def test_list_documents_returns_tenant_scoped_documents() -> None:
    session = AsyncMock()

    current_user = build_current_user()
    knowledge_base = build_knowledge_base()

    session.get.return_value = knowledge_base

    document = build_document()

    result = MagicMock()
    scalars = MagicMock()
    scalars.all.return_value = [document]
    result.scalars.return_value = scalars

    session.execute.return_value = result

    override_dependencies(session, current_user)

    try:
        with TestClient(app) as client:
            response = client.get(f"/knowledge-bases/{KNOWLEDGE_BASE_ID}/documents")

        assert response.status_code == 200

        body = response.json()

        assert len(body) == 1
        assert body[0]["id"] == str(DOCUMENT_ID)
        assert body[0]["organization_id"] == str(ORGANIZATION_ID)
        assert body[0]["knowledge_base_id"] == str(KNOWLEDGE_BASE_ID)

        session.execute.assert_awaited_once()

    finally:
        clear_overrides()


def test_get_document_returns_same_tenant_document() -> None:
    session = AsyncMock()

    current_user = build_current_user()
    knowledge_base = build_knowledge_base()
    document = build_document()

    session.get.return_value = knowledge_base

    result = MagicMock()
    result.scalar_one_or_none.return_value = document
    session.execute.return_value = result

    override_dependencies(session, current_user)

    try:
        with TestClient(app) as client:
            response = client.get(f"/knowledge-bases/{KNOWLEDGE_BASE_ID}/documents/{DOCUMENT_ID}")

        assert response.status_code == 200
        assert response.json()["id"] == str(DOCUMENT_ID)

    finally:
        clear_overrides()


def test_get_document_returns_404_for_cross_tenant_document() -> None:
    session = AsyncMock()

    current_user = build_current_user()
    knowledge_base = build_knowledge_base()

    session.get.return_value = knowledge_base

    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    session.execute.return_value = result

    override_dependencies(session, current_user)

    try:
        with TestClient(app) as client:
            response = client.get(
                f"/knowledge-bases/{KNOWLEDGE_BASE_ID}/documents/{OTHER_DOCUMENT_ID}"
            )

        assert response.status_code == 404
        assert response.json() == {
            "detail": "Document not found",
        }

    finally:
        clear_overrides()


def test_update_document_updates_same_tenant_document() -> None:
    session = AsyncMock()

    current_user = build_current_user()
    knowledge_base = build_knowledge_base()
    document = build_document()

    session.get.return_value = knowledge_base

    result = MagicMock()
    result.scalar_one_or_none.return_value = document
    session.execute.return_value = result

    override_dependencies(session, current_user)

    try:
        with TestClient(app) as client:
            response = client.patch(
                f"/knowledge-bases/{KNOWLEDGE_BASE_ID}/documents/{DOCUMENT_ID}",
                json={
                    "name": "updated-architecture.pdf",
                },
            )

        assert response.status_code == 200
        assert document.name == "updated-architecture.pdf"

        session.commit.assert_awaited_once()
        session.refresh.assert_awaited_once_with(document)

    finally:
        clear_overrides()


def test_update_document_returns_404_for_cross_tenant_document() -> None:
    session = AsyncMock()

    current_user = build_current_user()
    knowledge_base = build_knowledge_base()

    session.get.return_value = knowledge_base

    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    session.execute.return_value = result

    override_dependencies(session, current_user)

    try:
        with TestClient(app) as client:
            response = client.patch(
                f"/knowledge-bases/{KNOWLEDGE_BASE_ID}/documents/{OTHER_DOCUMENT_ID}",
                json={
                    "name": "attempted-update.pdf",
                },
            )

        assert response.status_code == 404
        assert response.json() == {
            "detail": "Document not found",
        }

        session.commit.assert_not_awaited()
        session.refresh.assert_not_awaited()

    finally:
        clear_overrides()


def test_delete_document_returns_204() -> None:
    session = AsyncMock()

    current_user = build_current_user()
    knowledge_base = build_knowledge_base()
    document = build_document()

    session.get.return_value = knowledge_base

    result = MagicMock()
    result.scalar_one_or_none.return_value = document
    session.execute.return_value = result

    override_dependencies(session, current_user)

    try:
        with TestClient(app) as client:
            response = client.delete(
                f"/knowledge-bases/{KNOWLEDGE_BASE_ID}/documents/{DOCUMENT_ID}"
            )

        assert response.status_code == 204

        session.delete.assert_awaited_once_with(document)
        session.commit.assert_awaited_once()

    finally:
        clear_overrides()


def test_delete_document_returns_404_for_cross_tenant_document() -> None:
    session = AsyncMock()

    current_user = build_current_user()
    knowledge_base = build_knowledge_base()

    session.get.return_value = knowledge_base

    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    session.execute.return_value = result

    override_dependencies(session, current_user)

    try:
        with TestClient(app) as client:
            response = client.delete(
                f"/knowledge-bases/{KNOWLEDGE_BASE_ID}/documents/{OTHER_DOCUMENT_ID}"
            )

        assert response.status_code == 404
        assert response.json() == {
            "detail": "Document not found",
        }

        session.delete.assert_not_awaited()
        session.commit.assert_not_awaited()

    finally:
        clear_overrides()
