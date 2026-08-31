from collections.abc import AsyncIterator
from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from enterprise_ai.api.dependencies import get_current_user
from enterprise_ai.core.security import hash_password
from enterprise_ai.main import create_app
from enterprise_ai.persistence.database import get_db_session
from enterprise_ai.persistence.models.organization import Organization
from enterprise_ai.persistence.models.user import User

ORGANIZATION_ID = UUID("11111111-1111-1111-1111-111111111111")
USER_ID = UUID("22222222-2222-2222-2222-222222222222")


def test_create_user_returns_created_user() -> None:
    session = AsyncMock(spec=AsyncSession)

    organization = Organization(
        id=ORGANIZATION_ID,
        name="Test Organization",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    session.get.return_value = organization

    async def refresh(user: User) -> None:
        user.id = USER_ID
        user.created_at = datetime.now(UTC)
        user.updated_at = datetime.now(UTC)

    session.refresh.side_effect = refresh

    async def override_db_session() -> AsyncIterator[AsyncSession]:
        yield session

    app = create_app()
    app.dependency_overrides[get_db_session] = override_db_session

    client = TestClient(app)

    response = client.post(
        "/users",
        json={
            "name": "Test User",
            "email": "test.user@example.com",
            "password": "StrongPass123!",
            "organization_id": str(ORGANIZATION_ID),
        },
    )

    assert response.status_code == 201
    assert response.json()["id"] == str(USER_ID)
    assert response.json()["name"] == "Test User"
    assert response.json()["email"] == "test.user@example.com"
    assert response.json()["organization_id"] == str(ORGANIZATION_ID)

    # Security: plaintext password and password hash must never be exposed.
    assert "password" not in response.json()
    assert "password_hash" not in response.json()

    # Verify that the password was hashed before persistence.
    added_user = session.add.call_args.args[0]

    assert added_user.password_hash != "StrongPass123!"
    assert added_user.password_hash.startswith("$argon2")

    session.commit.assert_awaited_once()


def test_create_user_returns_404_when_organization_not_found() -> None:
    session = AsyncMock(spec=AsyncSession)
    session.get.return_value = None

    async def override_db_session() -> AsyncIterator[AsyncSession]:
        yield session

    app = create_app()
    app.dependency_overrides[get_db_session] = override_db_session

    client = TestClient(app)

    response = client.post(
        "/users",
        json={
            "name": "Test User",
            "email": "test.user@example.com",
            "password": "StrongPass123!",
            "organization_id": str(ORGANIZATION_ID),
        },
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Organization not found",
    }

    session.commit.assert_not_awaited()


def test_create_user_returns_409_when_email_exists() -> None:
    session = AsyncMock(spec=AsyncSession)

    organization = Organization(
        id=ORGANIZATION_ID,
        name="Test Organization",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    session.get.return_value = organization
    session.commit.side_effect = IntegrityError(
        statement="INSERT INTO users",
        params={},
        orig=Exception("duplicate email"),
    )

    async def override_db_session() -> AsyncIterator[AsyncSession]:
        yield session

    app = create_app()
    app.dependency_overrides[get_db_session] = override_db_session

    client = TestClient(app)

    response = client.post(
        "/users",
        json={
            "name": "Test User",
            "email": "test.user@example.com",
            "password": "StrongPass123!",
            "organization_id": str(ORGANIZATION_ID),
        },
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Email already exists",
    }

    session.rollback.assert_awaited_once()


def test_get_user_returns_user() -> None:
    session = AsyncMock(spec=AsyncSession)

    user = User(
        id=USER_ID,
        name="Test User",
        email="test.user@example.com",
        organization_id=ORGANIZATION_ID,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    session.get.return_value = user

    async def override_db_session() -> AsyncIterator[AsyncSession]:
        yield session

    app = create_app()
    app.dependency_overrides[get_db_session] = override_db_session

    client = TestClient(app)

    response = client.get(f"/users/{USER_ID}")

    assert response.status_code == 200
    assert response.json()["id"] == str(USER_ID)
    assert response.json()["name"] == "Test User"
    assert response.json()["email"] == "test.user@example.com"
    assert response.json()["organization_id"] == str(ORGANIZATION_ID)


def test_get_user_returns_404_when_not_found() -> None:
    session = AsyncMock(spec=AsyncSession)
    session.get.return_value = None

    async def override_db_session() -> AsyncIterator[AsyncSession]:
        yield session

    app = create_app()
    app.dependency_overrides[get_db_session] = override_db_session

    client = TestClient(app)

    response = client.get(f"/users/{USER_ID}")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "User not found",
    }


def test_list_users_rejects_limit_above_maximum() -> None:
    current_user = User(
        id=USER_ID,
        name="Test User",
        email="test.user@example.com",
        password_hash=hash_password("StrongPass123!"),
        organization_id=ORGANIZATION_ID,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    async def override_current_user() -> User:
        return current_user

    app = create_app()
    app.dependency_overrides[get_current_user] = override_current_user

    client = TestClient(app)

    response = client.get("/users?limit=101&offset=0")

    assert response.status_code == 422


def test_update_user_returns_updated_user() -> None:
    session = AsyncMock(spec=AsyncSession)

    user = User(
        id=USER_ID,
        name="Old Name",
        email="old@example.com",
        organization_id=ORGANIZATION_ID,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    session.get.return_value = user

    async def refresh(updated_user: User) -> None:
        updated_user.updated_at = datetime.now(UTC)

    session.refresh.side_effect = refresh

    async def override_db_session() -> AsyncIterator[AsyncSession]:
        yield session

    app = create_app()
    app.dependency_overrides[get_db_session] = override_db_session

    client = TestClient(app)

    response = client.patch(
        f"/users/{USER_ID}",
        json={"name": "Updated Name"},
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Updated Name"
    assert response.json()["email"] == "old@example.com"

    session.commit.assert_awaited_once()
    session.refresh.assert_awaited_once()


def test_update_user_returns_404_when_not_found() -> None:
    session = AsyncMock(spec=AsyncSession)
    session.get.return_value = None

    async def override_db_session() -> AsyncIterator[AsyncSession]:
        yield session

    app = create_app()
    app.dependency_overrides[get_db_session] = override_db_session

    client = TestClient(app)

    response = client.patch(
        f"/users/{USER_ID}",
        json={"name": "Updated Name"},
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "User not found",
    }

    session.commit.assert_not_awaited()


def test_update_user_returns_409_when_email_exists() -> None:
    session = AsyncMock(spec=AsyncSession)

    user = User(
        id=USER_ID,
        name="Test User",
        email="original@example.com",
        organization_id=ORGANIZATION_ID,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    session.get.return_value = user
    session.commit.side_effect = IntegrityError(
        statement="UPDATE users",
        params={},
        orig=Exception("duplicate email"),
    )

    async def override_db_session() -> AsyncIterator[AsyncSession]:
        yield session

    app = create_app()
    app.dependency_overrides[get_db_session] = override_db_session

    client = TestClient(app)

    response = client.patch(
        f"/users/{USER_ID}",
        json={"email": "Existing@Example.com"},
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Email already exists",
    }

    session.rollback.assert_awaited_once()


def test_delete_user_returns_204() -> None:
    session = AsyncMock(spec=AsyncSession)

    user = User(
        id=USER_ID,
        name="Test User",
        email="test.user@example.com",
        organization_id=ORGANIZATION_ID,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    session.get.return_value = user

    async def override_db_session() -> AsyncIterator[AsyncSession]:
        yield session

    app = create_app()
    app.dependency_overrides[get_db_session] = override_db_session

    client = TestClient(app)

    response = client.delete(f"/users/{USER_ID}")

    assert response.status_code == 204
    assert response.content == b""

    session.delete.assert_awaited_once_with(user)
    session.commit.assert_awaited_once()


def test_delete_user_returns_404_when_not_found() -> None:
    session = AsyncMock(spec=AsyncSession)
    session.get.return_value = None

    async def override_db_session() -> AsyncIterator[AsyncSession]:
        yield session

    app = create_app()
    app.dependency_overrides[get_db_session] = override_db_session

    client = TestClient(app)

    response = client.delete(f"/users/{USER_ID}")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "User not found",
    }

    session.delete.assert_not_awaited()
    session.commit.assert_not_awaited()
