from fastapi.testclient import TestClient

from app.main import app


def test_client_log_accepts_frontend_diagnostics() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/client/log",
            json={
                "level": "error",
                "message": "fetch failed",
                "details": {"url": "/rtc/config", "status": 503},
            },
        )

    assert response.status_code == 200
    assert response.json() == {"ok": True}
