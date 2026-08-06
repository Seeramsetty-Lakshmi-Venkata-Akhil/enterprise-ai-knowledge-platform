from fastapi.testclient import TestClient

from enterprise_ai.main import create_app


def test_health_check_returns_healthy_status() -> None:
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}