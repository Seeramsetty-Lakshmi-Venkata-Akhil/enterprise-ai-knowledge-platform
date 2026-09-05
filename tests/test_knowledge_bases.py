from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

from fastapi.testclient import TestClient

from enterprise_ai.api.dependencies import get_current_user
from enterprise_ai.main import app
from enterprise_ai.persistence.database import get_db_session
from enterprise_ai.persistence.models.knowledge_base import KnowledgeBase
from enterprise_ai.persistence.models.user import User

ORGANIZATION_ID = UUID("281db554-5082-4452-a3d4-6f8902ea161b")
ORGANIZATION_B_ID = UUID("33333333-3333-3333-3333-333333333333")

USER_ID = UUID("da3926a6-0a7b-4069-8f55-b339edb0fa76")

KNOWLEDGE_BASE_ID = UUID("19281b5d-2be0-4dd0-aa49-caf3df612095")

KNOWLEDGE_BASE_B_ID = UUID("44444444-4444-4444-4444-444444444444")


def build_current_user() -> User:
    return User(
        id=USER_ID,
        name="Akhil",
        email="akhil@example.com",
        password_hash="hashed-password",
        organization_id=ORGANIZATION_ID,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def build_knowledge_base(
    *,
    knowledge_base_id: UUID = KNOWLEDGE_BASE_ID,
    organization_id: UUID = ORGANIZATION_ID,
) -> KnowledgeBase:
    return KnowledgeBase(
        id=knowledge_base_id,
        name="Enterprise AI Knowledge Base",
        description="Backend and AI engineering documentation",
        organization_id=organization_id,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def override_current_user() -> User:
    return build_current_user()


def create_session_mock() -> AsyncMock:
    session = AsyncMock()
    session.add = MagicMock()

    return session


client = TestClient(app)


def test_create_knowledge_base_uses_current_user_organization() -> None:
    session = create_session_mock()

    async def override_session():
        yield session

    app.dependency_overrides[get_db_session] = override_session
    app.dependency_overrides[get_current_user] = override_current_user

    async def refresh_side_effect(
        knowledge_base: KnowledgeBase,
    ) -> None:
        knowledge_base.id = KNOWLEDGE_BASE_ID
        knowledge_base.created_at = datetime.now(UTC)
        knowledge_base.updated_at = datetime.now(UTC)

    session.refresh.side_effect = refresh_side_effect

    response = client.post(
        "/knowledge-bases",
        json={
            "name": "Enterprise AI Knowledge Base",
            "description": "Backend and AI engineering documentation",
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert body["organization_id"] == str(ORGANIZATION_ID)
    assert body["name"] == "Enterprise AI Knowledge Base"

    session.commit.assert_awaited_once()

    app.dependency_overrides.clear()


def test_get_knowledge_base_returns_same_tenant_resource() -> None:
    session = create_session_mock()
    session.get.return_value = build_knowledge_base()

    async def override_session():
        yield session

    app.dependency_overrides[get_db_session] = override_session
    app.dependency_overrides[get_current_user] = override_current_user

    response = client.get(f"/knowledge-bases/{KNOWLEDGE_BASE_ID}")

    assert response.status_code == 200
    assert response.json()["id"] == str(KNOWLEDGE_BASE_ID)

    app.dependency_overrides.clear()


def test_get_knowledge_base_returns_404_for_different_organization() -> None:
    session = create_session_mock()

    session.get.return_value = build_knowledge_base(
        knowledge_base_id=KNOWLEDGE_BASE_B_ID,
        organization_id=ORGANIZATION_B_ID,
    )

    async def override_session():
        yield session

    app.dependency_overrides[get_db_session] = override_session
    app.dependency_overrides[get_current_user] = override_current_user

    response = client.get(f"/knowledge-bases/{KNOWLEDGE_BASE_B_ID}")

    assert response.status_code == 404
    assert response.json() == {"detail": "Knowledge base not found"}

    app.dependency_overrides.clear()


def test_update_knowledge_base_returns_404_for_different_organization() -> None:
    session = create_session_mock()

    session.get.return_value = build_knowledge_base(
        knowledge_base_id=KNOWLEDGE_BASE_B_ID,
        organization_id=ORGANIZATION_B_ID,
    )

    async def override_session():
        yield session

    app.dependency_overrides[get_db_session] = override_session
    app.dependency_overrides[get_current_user] = override_current_user

    response = client.patch(
        f"/knowledge-bases/{KNOWLEDGE_BASE_B_ID}",
        json={
            "name": "Should Not Update",
        },
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Knowledge base not found"}

    session.commit.assert_not_awaited()

    app.dependency_overrides.clear()


def test_delete_knowledge_base_returns_204() -> None:
    session = create_session_mock()
    knowledge_base = build_knowledge_base()

    session.get.return_value = knowledge_base

    async def override_session():
        yield session

    app.dependency_overrides[get_db_session] = override_session
    app.dependency_overrides[get_current_user] = override_current_user

    response = client.delete(f"/knowledge-bases/{KNOWLEDGE_BASE_ID}")

    assert response.status_code == 204

    session.delete.assert_awaited_once_with(knowledge_base)
    session.commit.assert_awaited_once()

    app.dependency_overrides.clear()


def test_delete_knowledge_base_returns_404_for_different_organization() -> None:
    session = create_session_mock()

    session.get.return_value = build_knowledge_base(
        knowledge_base_id=KNOWLEDGE_BASE_B_ID,
        organization_id=ORGANIZATION_B_ID,
    )

    async def override_session():
        yield session

    app.dependency_overrides[get_db_session] = override_session
    app.dependency_overrides[get_current_user] = override_current_user

    response = client.delete(f"/knowledge-bases/{KNOWLEDGE_BASE_B_ID}")

    assert response.status_code == 404
    assert response.json() == {"detail": "Knowledge base not found"}

    session.delete.assert_not_awaited()
    session.commit.assert_not_awaited()

    app.dependency_overrides.clear()
