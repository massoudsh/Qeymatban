from fastapi.testclient import TestClient

from app.db import Base, Property, SessionLocal, Valuation, engine
from app.main import app


class FakeValuationService:
    model_version = "test-v1"

    def valuate(self, _frame):
        return {
            "price_low": 90_000_000,
            "price_mid": 100_000_000,
            "price_high": 110_000_000,
            "confidence_level": 0.8,
            "model_version": self.model_version,
            "feature_contributions": {"area_sqm": 10_000_000},
            "comparables": [],
        }


def setup_function():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    app.state.valuation_service = FakeValuationService()


def test_create_valuation_persists_property_and_result():
    client = TestClient(app)

    response = client.post(
        "/v1/valuations",
        json={
            "title": "واحد تست",
            "neighborhood": "نیاوران",
            "city": "تهران",
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
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["valuation_id"]
    assert payload["model_version"] == "test-v1"

    with SessionLocal() as session:
        valuation = session.get(Valuation, payload["valuation_id"])
        property_record = session.get(Property, valuation.property_id)

    assert property_record.title == "واحد تست"
    assert property_record.neighborhood == "نیاوران"
    assert valuation.price_mid == 100_000_000
    assert valuation.shap_values == {"area_sqm": 10_000_000}
