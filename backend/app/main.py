import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

import pandas as pd
from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware

from app.ml.valuation_service import ValuationService
from app.schemas.valuation import ModelStatusResponse, PropertyFeatures, ValuationResponse


def _configured_api_keys() -> set[str]:
    return {key.strip() for key in os.getenv("QEYMATBAN_API_KEYS", "").split(",") if key.strip()}


def require_api_key(x_api_key: Annotated[str | None, Header()] = None) -> None:
    keys = _configured_api_keys()
    if keys and x_api_key not in keys:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API key نامعتبر است")


@asynccontextmanager
async def lifespan(app: FastAPI):
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


@app.post(
    "/v1/valuations",
    response_model=ValuationResponse,
    dependencies=[Depends(require_api_key)],
)
def create_valuation(features: PropertyFeatures, request: Request) -> ValuationResponse:
    service = request.app.state.valuation_service
    if service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="مدل آماده نیست؛ ابتدا pipeline آموزش را اجرا کنید",
        )

    frame = pd.DataFrame([features.model_dump()])
    return ValuationResponse.model_validate(service.valuate(frame))
