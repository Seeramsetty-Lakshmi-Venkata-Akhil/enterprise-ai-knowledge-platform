from collections.abc import AsyncIterator
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from enterprise_ai.main import create_app
from enterprise_ai.persistence.database import get_db_session


async def override_db_session() -> AsyncIterator[AsyncSession]:
    session = AsyncMock(spec=AsyncSession)
    yield session


def test_health_check_returns_healthy_status() -> None:
    app = create_app()
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_readiness_check_returns_ready_status() -> None:
    app = create_app()
    app.dependency_overrides[get_db_session] = override_db_session
    client = TestClient(app)

    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


async def override_failing_db_session() -> AsyncIterator[AsyncSession]:
    session = AsyncMock(spec=AsyncSession)
    session.execute.side_effect = RuntimeError("Database unavailable")
    yield session


def test_readiness_check_returns_503_when_database_is_unavailable() -> None:
    app = create_app()
    app.dependency_overrides[get_db_session] = override_failing_db_session
    client = TestClient(app)

    response = client.get("/ready")

    assert response.status_code == 503
    assert response.json() == {"detail": "Database unavailable"}
