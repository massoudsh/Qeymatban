from fastapi.testclient import TestClient

from app.main import app

VALID_PROPERTY = {
    "area_sqm": 92,
    "year_built": 1397,
    "floor": 3,
    "total_floors": 6,
    "rooms": 2,
    "has_parking": True,
    "has_elevator": True,
    "has_storage": True,
    "renovated": False,
    "light_score": 4,
    "view_score": 3,
    "access_score": 4,
}


def test_model_status_reports_missing_artifact(monkeypatch, tmp_path):
    monkeypatch.setenv("QEYMATBAN_MODEL_PATH", str(tmp_path / "missing.joblib"))
    with TestClient(app) as client:
        assert client.get("/v1/model/status").json() == {"ready": False, "model_version": None}
        assert client.post("/v1/valuations", json=VALID_PROPERTY).status_code == 503


def test_api_key_is_required_when_configured(monkeypatch, tmp_path):
    monkeypatch.setenv("QEYMATBAN_MODEL_PATH", str(tmp_path / "missing.joblib"))
    monkeypatch.setenv("QEYMATBAN_API_KEYS", "secret-key")
    with TestClient(app) as client:
        assert client.post("/v1/valuations", json=VALID_PROPERTY).status_code == 401
        response = client.post("/v1/valuations", json=VALID_PROPERTY, headers={"X-API-Key": "secret-key"})
        assert response.status_code == 503
