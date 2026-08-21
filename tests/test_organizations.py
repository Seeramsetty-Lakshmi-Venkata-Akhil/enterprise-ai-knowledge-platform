from collections.abc import AsyncIterator
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
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


def test_list_organizations_returns_organizations() -> None:
    session = AsyncMock(spec=AsyncSession)

    organization = Organization(
        id=ORGANIZATION_ID,
        name="Test Organization",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    result = MagicMock()
    result.scalars.return_value.all.return_value = [organization]

    session.execute.return_value = result

    async def override_list_db_session() -> AsyncIterator[AsyncSession]:
        yield session

    app = create_app()
    app.dependency_overrides[get_db_session] = override_list_db_session

    client = TestClient(app)

    response = client.get("/organizations")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == "Test Organization"


def test_update_organization_returns_updated_organization() -> None:
    session = AsyncMock(spec=AsyncSession)

    organization = Organization(
        id=ORGANIZATION_ID,
        name="Old Name",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    session.get.return_value = organization

    async def refresh(updated_organization: Organization) -> None:
        updated_organization.updated_at = datetime.now(UTC)

    session.refresh.side_effect = refresh

    async def override_update_db_session() -> AsyncIterator[AsyncSession]:
        yield session

    app = create_app()
    app.dependency_overrides[get_db_session] = override_update_db_session

    client = TestClient(app)

    response = client.patch(
        f"/organizations/{ORGANIZATION_ID}",
        json={"name": "Updated Name"},
    )

    assert response.status_code == 200
    assert response.json()["id"] == str(ORGANIZATION_ID)
    assert response.json()["name"] == "Updated Name"

    session.commit.assert_awaited_once()


def test_update_organization_returns_404_when_not_found() -> None:
    session = AsyncMock(spec=AsyncSession)
    session.get.return_value = None

    async def override_update_db_session() -> AsyncIterator[AsyncSession]:
        yield session

    app = create_app()
    app.dependency_overrides[get_db_session] = override_update_db_session

    client = TestClient(app)

    response = client.patch(
        f"/organizations/{ORGANIZATION_ID}",
        json={"name": "Updated Name"},
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Organization not found",
    }


def test_update_organization_returns_409_when_name_exists() -> None:
    session = AsyncMock(spec=AsyncSession)

    organization = Organization(
        id=ORGANIZATION_ID,
        name="Old Name",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    session.get.return_value = organization
    session.commit.side_effect = IntegrityError(
        statement=None,
        params=None,
        orig=Exception("duplicate organization"),
    )

    async def override_update_db_session() -> AsyncIterator[AsyncSession]:
        yield session

    app = create_app()
    app.dependency_overrides[get_db_session] = override_update_db_session

    client = TestClient(app)

    response = client.patch(
        f"/organizations/{ORGANIZATION_ID}",
        json={"name": "Existing Organization"},
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Organization already exists",
    }

    session.rollback.assert_awaited_once()


def test_delete_organization_returns_204() -> None:
    session = AsyncMock(spec=AsyncSession)

    organization = Organization(
        id=ORGANIZATION_ID,
        name="Test Organization",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    session.get.return_value = organization

    async def override_delete_db_session() -> AsyncIterator[AsyncSession]:
        yield session

    app = create_app()
    app.dependency_overrides[get_db_session] = override_delete_db_session

    client = TestClient(app)

    response = client.delete(f"/organizations/{ORGANIZATION_ID}")

    assert response.status_code == 204
    assert response.content == b""

    session.delete.assert_awaited_once_with(organization)
    session.commit.assert_awaited_once()


def test_delete_organization_returns_404_when_not_found() -> None:
    session = AsyncMock(spec=AsyncSession)
    session.get.return_value = None

    async def override_delete_db_session() -> AsyncIterator[AsyncSession]:
        yield session

    app = create_app()
    app.dependency_overrides[get_db_session] = override_delete_db_session

    client = TestClient(app)

    response = client.delete(f"/organizations/{ORGANIZATION_ID}")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Organization not found",
    }

    session.delete.assert_not_awaited()
    session.commit.assert_not_awaited()
