import os
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Annotated

import pandas as pd
from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware

from app.db import Property, SessionLocal, Valuation, ValuationComparable, create_tables, seed_demo_properties
from app.ml.valuation_service import ValuationService
from app.schemas.valuation import (
    DashboardStatsResponse,
    ModelStatusResponse,
    PropertyFeatures,
    ValuationHistoryItem,
    ValuationHistoryResponse,
    ValuationRequest,
    ValuationResponse,
)


def _configured_api_keys() -> set[str]:
    return {key.strip() for key in os.getenv("QEYMATBAN_API_KEYS", "").split(",") if key.strip()}


def require_api_key(x_api_key: Annotated[str | None, Header()] = None) -> None:
    keys = _configured_api_keys()
    if keys and x_api_key not in keys:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API key نامعتبر است")


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    seed_demo_properties()
    model_path = Path(os.getenv("QEYMATBAN_MODEL_PATH", "models/current.joblib"))
    app.state.valuation_service = ValuationService.load(model_path) if model_path.is_file() else None
    yield


app = FastAPI(
    title="Qeymatban API",
    description="ارزش‌گذاری توضیح‌پذیر املاک ایران",
    version="0.1.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in os.getenv("QEYMATBAN_CORS_ORIGINS", "http://localhost:3000").split(",")],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-API-Key"],
)


def _history_item(valuation: Valuation, property_record: Property) -> ValuationHistoryItem:
    return ValuationHistoryItem(
        valuation_id=valuation.id,
        property_id=property_record.id,
        title=property_record.title,
        neighborhood=property_record.neighborhood,
        created_at=valuation.created_at.isoformat(),
        price_low=valuation.price_low,
        price_mid=valuation.price_mid,
        price_high=valuation.price_high,
        confidence_level=valuation.confidence_level,
        model_version=valuation.model_version,
    )


def _persist_valuation(features: ValuationRequest, result: dict) -> str:
    with SessionLocal() as session:
        property_record = Property(**features.model_dump())
        session.add(property_record)
        session.flush()

        valuation = Valuation(
            property_id=property_record.id,
            price_low=result["price_low"],
            price_mid=result["price_mid"],
            price_high=result["price_high"],
            confidence_level=result["confidence_level"],
            shap_values=result["feature_contributions"],
            model_version=result["model_version"],
        )
        session.add(valuation)
        session.flush()

        comparable_ids = [item["id"] for item in result["comparables"]]
        existing_ids = set(session.query(Property.id).filter(Property.id.in_(comparable_ids)).all())
        existing_ids = {row[0] for row in existing_ids}
        for rank, comparable in enumerate(result["comparables"], start=1):
            if comparable["id"] in existing_ids:
                session.add(
                    ValuationComparable(
                        valuation_id=valuation.id,
                        comparable_id=comparable["id"],
                        similarity=comparable["similarity"],
                        rank=rank,
                    )
                )
        session.commit()
        return valuation.id


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/v1/model/status", response_model=ModelStatusResponse)
def model_status(request: Request) -> ModelStatusResponse:
    service = request.app.state.valuation_service
    return ModelStatusResponse(
        ready=service is not None,
        model_version=service.model_version if service else None,
    )


@app.get(
    "/v1/valuations/stats",
    response_model=DashboardStatsResponse,
    dependencies=[Depends(require_api_key)],
)
def valuation_stats() -> DashboardStatsResponse:
    thirty_days_ago = datetime.now(UTC) - timedelta(days=30)
    with SessionLocal() as session:
        all_valuations = session.query(Valuation).all()
    mids = sorted(item.price_mid for item in all_valuations)
    median = mids[len(mids) // 2] if mids else None
    return DashboardStatsResponse(
        total_valuations=len(all_valuations),
        average_confidence=(
            sum(item.confidence_level for item in all_valuations) / len(all_valuations) if all_valuations else None
        ),
        last_30_days=sum(1 for item in all_valuations if item.created_at.replace(tzinfo=UTC) >= thirty_days_ago),
        median_price_mid=median,
    )


@app.get(
    "/v1/valuations",
    response_model=ValuationHistoryResponse,
    dependencies=[Depends(require_api_key)],
)
def list_valuations(limit: int = 20) -> ValuationHistoryResponse:
    with SessionLocal() as session:
        rows = (
            session.query(Valuation, Property)
            .join(Property, Valuation.property_id == Property.id)
            .order_by(Valuation.created_at.desc())
            .limit(max(1, min(limit, 100)))
            .all()
        )
    return ValuationHistoryResponse(items=[_history_item(valuation, property_record) for valuation, property_record in rows])


@app.post(
    "/v1/valuations",
    response_model=ValuationResponse,
    dependencies=[Depends(require_api_key)],
)
def create_valuation(features: ValuationRequest, request: Request) -> ValuationResponse:
    service = request.app.state.valuation_service
    if service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="مدل آماده نیست؛ ابتدا pipeline آموزش را اجرا کنید",
        )

    feature_frame = pd.DataFrame([PropertyFeatures.model_validate(features.model_dump()).model_dump()])
    result = service.valuate(feature_frame)
    result["valuation_id"] = _persist_valuation(features, result)
    return ValuationResponse.model_validate(result)
