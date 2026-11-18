from datetime import datetime

from fastapi.testclient import TestClient

from app.db import Base, ModelVersion, SessionLocal, engine
from app.main import app


def setup_function():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def add_version(version: str, mape: float, promoted: bool, day: int) -> None:
    with SessionLocal() as session:
        session.add(
            ModelVersion(
                version=version,
                model_family="xgboost",
                artifact_path=f"models/valuation-{version}.joblib",
                trained_at=datetime(2026, 1, day),
                training_rows=100,
                validation_rows=25,
                mae=1_000_000.0,
                mape=mape,
                dataset_sha256="a" * 64,
                data_source="transactions table",
                promoted=promoted,
            )
        )
        session.commit()


def test_model_versions_returns_current_and_delta():
    add_version("v1", 0.20, promoted=True, day=1)
    add_version("v2", 0.15, promoted=False, day=2)

    response = TestClient(app).get("/v1/model/versions")

    assert response.status_code == 200
    payload = response.json()
    assert payload["current"] == "v1"
    # Newest first, and v2 is the comparison point for the promoted v1.
    assert [item["version"] for item in payload["items"]] == ["v2", "v1"]
    assert payload["mape_delta"] == 0.20 - 0.15


def test_model_versions_empty_registry():
    response = TestClient(app).get("/v1/model/versions")

    assert response.status_code == 200
    assert response.json() == {"current": None, "items": [], "mape_delta": None}
