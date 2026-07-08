from fastapi.testclient import TestClient

from main import app


def test_list_vendors_returns_seed_data_without_database() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/vendors")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 4
    assert payload[0]["id"] == "VEN-0042"
