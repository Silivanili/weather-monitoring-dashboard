from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_does_not_require_database(monkeypatch):
    def database_must_not_be_checked():
        raise AssertionError("Database must not be checked by /health")

    monkeypatch.setattr(
        "app.main.check_database_connection",
        database_must_not_be_checked,
    )

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_returns_200_when_database_is_available(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.main.check_database_connection",
        lambda: True,
    )

    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_ready_returns_503_when_database_is_unavailable(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.main.check_database_connection",
        lambda: False,
    )

    response = client.get("/ready")

    assert response.status_code == 503
    assert response.json() == {
        "detail": "Database unavailable",
    }
