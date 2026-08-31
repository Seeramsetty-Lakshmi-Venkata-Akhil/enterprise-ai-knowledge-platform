from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import jwt
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from enterprise_ai.core.config import get_settings
from enterprise_ai.core.security import create_access_token, hash_password
from enterprise_ai.main import create_app
from enterprise_ai.persistence.database import get_db_session
from enterprise_ai.persistence.models.user import User

USER_ID = UUID("22222222-2222-2222-2222-222222222222")
ORGANIZATION_ID = UUID("11111111-1111-1111-1111-111111111111")


def test_login_returns_success_for_valid_credentials() -> None:
    session = AsyncMock(spec=AsyncSession)

    user = User(
        id=USER_ID,
        name="Test User",
        email="test.user@example.com",
        password_hash=hash_password("StrongPass123!"),
        organization_id=ORGANIZATION_ID,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    result = MagicMock()
    result.scalar_one_or_none.return_value = user
    session.execute.return_value = result

    async def override_db_session() -> AsyncIterator[AsyncSession]:
        yield session

    app = create_app()
    app.dependency_overrides[get_db_session] = override_db_session

    client = TestClient(app)

    response = client.post(
        "/auth/login",
        json={
            "email": "Test.User@Example.com",
            "password": "StrongPass123!",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["token_type"] == "bearer"
    assert "access_token" in body
    assert isinstance(body["access_token"], str)
    assert body["access_token"]

    settings = get_settings()

    payload = jwt.decode(
        body["access_token"],
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )

    assert payload["sub"] == str(USER_ID)
    assert payload["organization_id"] == str(ORGANIZATION_ID)
    assert "exp" in payload


def test_login_returns_401_for_wrong_password() -> None:
    session = AsyncMock(spec=AsyncSession)

    user = User(
        id=USER_ID,
        name="Test User",
        email="test.user@example.com",
        password_hash=hash_password("StrongPass123!"),
        organization_id=ORGANIZATION_ID,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    result = MagicMock()
    result.scalar_one_or_none.return_value = user
    session.execute.return_value = result

    async def override_db_session() -> AsyncIterator[AsyncSession]:
        yield session

    app = create_app()
    app.dependency_overrides[get_db_session] = override_db_session

    client = TestClient(app)

    response = client.post(
        "/auth/login",
        json={
            "email": "test.user@example.com",
            "password": "WrongPass123!",
        },
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Invalid email or password",
    }


def test_login_returns_401_for_unknown_email() -> None:
    session = AsyncMock(spec=AsyncSession)

    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    session.execute.return_value = result

    async def override_db_session() -> AsyncIterator[AsyncSession]:
        yield session

    app = create_app()
    app.dependency_overrides[get_db_session] = override_db_session

    client = TestClient(app)

    response = client.post(
        "/auth/login",
        json={
            "email": "unknown@example.com",
            "password": "StrongPass123!",
        },
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Invalid email or password",
    }


def test_get_me_returns_current_user_for_valid_token() -> None:
    session = AsyncMock(spec=AsyncSession)

    user = User(
        id=USER_ID,
        name="Test User",
        email="test.user@example.com",
        password_hash=hash_password("StrongPass123!"),
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

    token = create_access_token(
        user_id=USER_ID,
        organization_id=ORGANIZATION_ID,
    )

    response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200
    assert response.json()["id"] == str(USER_ID)
    assert response.json()["email"] == "test.user@example.com"
    assert response.json()["organization_id"] == str(ORGANIZATION_ID)

    assert "password" not in response.json()
    assert "password_hash" not in response.json()


def test_get_me_rejects_missing_token() -> None:
    app = create_app()
    client = TestClient(app)

    response = client.get("/auth/me")

    assert response.status_code in {401, 403}


def test_get_me_rejects_tampered_token() -> None:
    session = AsyncMock(spec=AsyncSession)

    async def override_db_session() -> AsyncIterator[AsyncSession]:
        yield session

    app = create_app()
    app.dependency_overrides[get_db_session] = override_db_session

    client = TestClient(app)

    token = create_access_token(
        user_id=USER_ID,
        organization_id=ORGANIZATION_ID,
    )

    header, payload, signature = token.split(".")

    # Tamper with the beginning of the signature instead of the
    # final Base64URL character.
    tampered_signature = ("A" if signature[0] != "A" else "B") + signature[1:]

    tampered_token = f"{header}.{payload}.{tampered_signature}"

    response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {tampered_token}",
        },
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Invalid or expired token",
    }

    # JWT validation should fail before the database is queried.
    session.get.assert_not_awaited()


def test_get_me_rejects_expired_token() -> None:
    session = AsyncMock(spec=AsyncSession)

    async def override_db_session() -> AsyncIterator[AsyncSession]:
        yield session

    app = create_app()
    app.dependency_overrides[get_db_session] = override_db_session

    client = TestClient(app)

    settings = get_settings()

    expired_token = jwt.encode(
        {
            "sub": str(USER_ID),
            "organization_id": str(ORGANIZATION_ID),
            "exp": datetime.now(UTC) - timedelta(minutes=1),
        },
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {expired_token}",
        },
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Invalid or expired token",
    }

    session.get.assert_not_awaited()


def test_get_me_rejects_token_when_user_no_longer_exists() -> None:
    session = AsyncMock(spec=AsyncSession)
    session.get.return_value = None

    async def override_db_session() -> AsyncIterator[AsyncSession]:
        yield session

    app = create_app()
    app.dependency_overrides[get_db_session] = override_db_session

    client = TestClient(app)

    token = create_access_token(
        user_id=USER_ID,
        organization_id=ORGANIZATION_ID,
    )

    response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Invalid or expired token",
    }

    session.get.assert_awaited_once()
