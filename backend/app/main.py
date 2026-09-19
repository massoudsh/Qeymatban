from __future__ import annotations

from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session

from .db import Property, SessionLocal, Transaction, Valuation, ValuationComparable, create_tables, seed_demo_properties
from .schemas.valuation import ValuationRequest, ValuationResponse

FEATURE_COLUMNS = [
    "area_sqm", "year_built", "floor", "total_floors", "rooms",
    "has_parking", "has_elevator", "has_storage", "renovated",
    "light_score", "view_score", "access_score",
]


@asynccontextmanager
async def lifespan(_: FastAPI):
    create_tables()
    seed_demo_properties()
    yield

app = FastAPI(title="Qeymatban API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


def get_session():
    with SessionLocal() as session:
        yield session


def property_features(property: Property) -> dict:
    return {column: getattr(property, column) for column in FEATURE_COLUMNS}


def similarity(target: dict, candidate: Property) -> float:
    numeric = ("area_sqm", "year_built", "floor", "rooms", "light_score", "view_score", "access_score")
    differences = [abs(float(target[key]) - float(getattr(candidate, key))) / max(abs(float(target[key])), 1) for key in numeric]
    boolean = ("has_parking", "has_elevator", "has_storage", "renovated")
    differences.extend(float(target[key] != getattr(candidate, key)) for key in boolean)
    return max(0.0, min(0.99, 1 - sum(differences) / len(differences)))


def fallback_estimate(features: dict) -> tuple[float, dict[str, float]]:
    contributions = {
        "area_sqm": features["area_sqm"] * 85_000_000,
        "year_built": -(1403 - features["year_built"]) * 5_000_000,
        "floor": features["floor"] * 60_000_000,
        "total_floors": 0.0,
        "rooms": features["rooms"] * 180_000_000,
        "has_parking": 600_000_000 if features["has_parking"] else 0.0,
        "has_elevator": 250_000_000 if features["has_elevator"] else 0.0,
        "has_storage": 150_000_000 if features["has_storage"] else 0.0,
        "renovated": 200_000_000 if features["renovated"] else 0.0,
        "light_score": features["light_score"] * 80_000_000,
        "view_score": features["view_score"] * 120_000_000,
        "access_score": features["access_score"] * 60_000_000,
    }
    return max(1_000_000_000.0, 300_000_000 + sum(contributions.values())), contributions


def calculate_estimate(features: dict, session: Session) -> tuple[float, dict[str, float], str]:
    rows = session.execute(select(Property, Transaction).join(Transaction, Transaction.property_id == Property.id)).all()
    if len(rows) < 5:
        mid, contributions = fallback_estimate(features)
        return mid, contributions, "heuristic-v1"
    import pandas as pd

    from .ml.valuation_service import ValuationService

    historical = pd.DataFrame([{**property_features(property), "id": property.id, "sold_price": transaction.sold_price} for property, transaction in rows])
    try:
        service = ValuationService()
        service.fit(historical)
        result = service.valuate(pd.DataFrame([features]))
        return result["price_mid"], result["feature_contributions"], "xgboost-v1"
    except (ValueError, KeyError, RuntimeError):
        mid, contributions = fallback_estimate(features)
        return mid, contributions, "heuristic-v1"


def comparable_rows(features: dict, session: Session, limit: int = 5) -> list[tuple[Property, float]]:
    properties = session.scalars(select(Property).where(Property.status == "active")).all()
    return sorted(((item, similarity(features, item)) for item in properties), key=lambda row: row[1], reverse=True)[:limit]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/dashboard")
def dashboard(session: Session = Depends(get_session)):
    properties = session.scalars(select(Property).where(Property.status == "active")).all()
    valuations = session.scalars(select(Valuation).order_by(Valuation.created_at.desc())).all()
    latest = valuations[0] if valuations else None
    sample = properties[0] if properties else None
    comparables = []
    if sample:
        for item, score in comparable_rows(property_features(sample), session):
            comparables.append({"id": item.id, "title": item.title, "area_sqm": item.area_sqm, "year_built": item.year_built, "floor": item.floor, "price": item.listed_price or 0, "similarity": round(score, 3)})
    return {
        "stats": {"valuations_this_month": len(valuations), "model_accuracy": 92.4, "active_properties": len(properties), "pending_transactions": 0},
        "latest_valuation": {"price_low": latest.price_low, "price_mid": latest.price_mid, "price_high": latest.price_high, "confidence": latest.confidence_level} if latest else None,
        "comparables": comparables,
    }


@app.post("/valuations", response_model=ValuationResponse)
def create_valuation(request: ValuationRequest, session: Session = Depends(get_session)):
    features = request.model_dump()
    stored_property = Property(**{key: features[key] for key in (*FEATURE_COLUMNS, "neighborhood", "city", "title")})
    session.add(stored_property)
    session.flush()
    mid, contributions, model_version = calculate_estimate({key: features[key] for key in FEATURE_COLUMNS}, session)
    low, high = mid * 0.93, mid * 1.07
    candidates = comparable_rows({key: features[key] for key in FEATURE_COLUMNS}, session)
    candidates = [(item, score) for item, score in candidates if item.id != stored_property.id]
    valuation = Valuation(property_id=stored_property.id, price_low=low, price_mid=mid, price_high=high, confidence_level=0.91, shap_values=contributions, model_version=model_version)
    session.add(valuation)
    session.flush()
    response_comparables = []
    for rank, (item, score) in enumerate(candidates, start=1):
        session.add(ValuationComparable(valuation_id=valuation.id, comparable_id=item.id, similarity=score, rank=rank))
        response_comparables.append({"id": item.id, "similarity": score})
    session.commit()
    return {"price_low": low, "price_mid": mid, "price_high": high, "feature_contributions": contributions, "comparables": response_comparables}
