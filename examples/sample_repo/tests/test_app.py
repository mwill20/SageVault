from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_widget_listing():
    response = client.get("/widgets")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["widgets"]) == 2
    assert payload["widgets"][0]["name"] == "Telemetry Primer"
