from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def api_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    database_path = tmp_path / "qeymatban.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database_path}")
    from app.main import app

    with TestClient(app) as client:
        yield client


def valuation_payload() -> dict:
    return {
        "neighborhood": "نیاوران",
        "city": "تهران",
        "title": "ملک آزمایشی",
        "area_sqm": 148,
        "year_built": 1400,
        "floor": 3,
        "total_floors": 5,
        "rooms": 3,
        "has_parking": True,
        "has_elevator": True,
        "has_storage": True,
        "renovated": True,
        "light_score": 5,
        "view_score": 4,
        "access_score": 5,
    }


def test_dashboard_is_seeded_and_valuation_is_persisted(api_client: TestClient):
    dashboard = api_client.get("/dashboard")
    assert dashboard.status_code == 200
    assert dashboard.json()["stats"]["active_properties"] == 6

    response = api_client.post("/valuations", json=valuation_payload())
    assert response.status_code == 200
    body = response.json()
    assert body["price_low"] < body["price_mid"] < body["price_high"]
    assert body["comparables"]

    refreshed = api_client.get("/dashboard").json()
    assert refreshed["stats"]["valuations_this_month"] == 1
    assert refreshed["latest_valuation"]["price_mid"] == body["price_mid"]
