from collections.abc import AsyncIterator
from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from enterprise_ai.main import create_app
from enterprise_ai.persistence.database import get_db_session
from enterprise_ai.persistence.models.organization import Organization

ORGANIZATION_ID = UUID("11111111-1111-1111-1111-111111111111")


async def override_db_session() -> AsyncIterator[AsyncSession]:
    session = AsyncMock(spec=AsyncSession)

    organization = Organization(
        id=ORGANIZATION_ID,
        name="Test Organization",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    session.get.return_value = organization

    yield session


def test_get_organization_returns_organization() -> None:
    app = create_app()
    app.dependency_overrides[get_db_session] = override_db_session

    client = TestClient(app)

    response = client.get(f"/organizations/{ORGANIZATION_ID}")

    assert response.status_code == 200
    assert response.json()["id"] == str(ORGANIZATION_ID)
    assert response.json()["name"] == "Test Organization"


def test_get_organization_returns_404_when_not_found() -> None:
    async def override_empty_db_session() -> AsyncIterator[AsyncSession]:
        session = AsyncMock(spec=AsyncSession)
        session.get.return_value = None

        yield session

    app = create_app()
    app.dependency_overrides[get_db_session] = override_empty_db_session

    client = TestClient(app)

    response = client.get(f"/organizations/{ORGANIZATION_ID}")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Organization not found",
    }


def test_create_organization_returns_created_organization() -> None:
    async def override_create_db_session() -> AsyncIterator[AsyncSession]:
        session = AsyncMock(spec=AsyncSession)

        async def refresh(organization: Organization) -> None:
            organization.id = ORGANIZATION_ID
            organization.created_at = datetime.now(UTC)
            organization.updated_at = datetime.now(UTC)

        session.refresh.side_effect = refresh

        yield session

    app = create_app()
    app.dependency_overrides[get_db_session] = override_create_db_session

    client = TestClient(app)

    response = client.post(
        "/organizations",
        json={"name": "Test Organization"},
    )

    assert response.status_code == 201
    assert response.json()["id"] == str(ORGANIZATION_ID)
    assert response.json()["name"] == "Test Organization"


def test_create_organization_returns_409_when_name_exists() -> None:
    session = AsyncMock(spec=AsyncSession)

    session.commit.side_effect = IntegrityError(
        statement=None,
        params=None,
        orig=Exception("duplicate organization"),
    )

    async def override_duplicate_db_session() -> AsyncIterator[AsyncSession]:
        yield session

    app = create_app()
    app.dependency_overrides[get_db_session] = override_duplicate_db_session

    client = TestClient(app)

    response = client.post(
        "/organizations",
        json={"name": "Existing Organization"},
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Organization already exists",
    }

    session.rollback.assert_awaited_once()
