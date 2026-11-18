"""Retraining, promotion, rollback and model-version registry behaviour."""

from pathlib import Path

import pandas as pd
import pytest

from app.db import Base, ModelVersion, SessionLocal, engine
from app.ml.pricing_pipeline import FEATURE_COLUMNS
from app.scripts.retrain import retrain, rollback


def synthetic_frame(rows: int = 60, price_scale: float = 1.0) -> pd.DataFrame:
    """Plausible transactions whose price is a deterministic function of the features."""
    records = []
    for index in range(rows):
        area = 60 + (index % 90)
        year_built = 1380 + (index % 24)
        floor = index % 8
        record = {
            "id": f"tx-{index:04d}",
            "neighborhood": ["نیاوران", "پونک", "چیتگر"][index % 3],
            "city": "تهران",
            "sold_date": f"2024-{1 + index % 12:02d}-{1 + index % 27:02d}",
            "area_sqm": area,
            "year_built": year_built,
            "floor": floor,
            "total_floors": max(floor + 1, 6),
            "rooms": 1 + area // 40,
            "has_parking": index % 2 == 0,
            "has_elevator": index % 3 != 0,
            "has_storage": index % 4 != 0,
            "renovated": index % 5 == 0,
            "light_score": 1 + index % 5,
            "view_score": 1 + (index + 2) % 5,
            "access_score": 1 + (index + 3) % 5,
        }
        base = area * 90_000_000 + (year_built - 1380) * 400_000_000 + floor * 120_000_000
        record["sold_price"] = float(base) * price_scale
        records.append(record)
    return pd.DataFrame(records)


def setup_function():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def write_csv(tmp_path, frame: pd.DataFrame) -> Path:
    path = tmp_path / "transactions.csv"
    frame.to_csv(path, index=False)
    return path


def test_retrain_promotes_first_version(tmp_path):
    data = write_csv(tmp_path, synthetic_frame())

    result = retrain(output_dir=tmp_path / "models", data_path=data, version="v1")

    assert result["promoted"] is True
    assert result["previous_version"] is None
    assert (tmp_path / "models" / "current.joblib").is_file()
    with SessionLocal() as session:
        rows = session.query(ModelVersion).all()
    assert [row.version for row in rows] == ["v1"]
    assert rows[0].promoted is True
    assert rows[0].dataset_sha256 and len(rows[0].dataset_sha256) == 64


def test_retrain_rejects_regression_and_keeps_current(tmp_path):
    good = write_csv(tmp_path, synthetic_frame())
    assert retrain(output_dir=tmp_path / "models", data_path=good, version="good")["promoted"] is True

    # Deliberately break the signal so validation error is far worse.
    noisy = synthetic_frame(price_scale=1.0)
    noisy["sold_price"] = noisy["sold_price"].sample(frac=1.0, random_state=0).to_numpy() * 4
    bad = write_csv(tmp_path, noisy)
    result = retrain(output_dir=tmp_path / "models", data_path=bad, version="bad", tolerance=0.0)

    assert result["promoted"] is False
    assert "rejected" in result["decision"]
    with SessionLocal() as session:
        promoted = session.query(ModelVersion).filter(ModelVersion.promoted.is_(True)).all()
    assert [row.version for row in promoted] == ["good"]


def test_retrain_force_promotes_a_regression(tmp_path):
    data = write_csv(tmp_path, synthetic_frame())
    retrain(output_dir=tmp_path / "models", data_path=data, version="v1")

    shuffled = synthetic_frame()
    shuffled["sold_price"] = shuffled["sold_price"].sample(frac=1.0, random_state=1).to_numpy() * 5
    result = retrain(
        output_dir=tmp_path / "models",
        data_path=write_csv(tmp_path, shuffled),
        version="v2",
        force=True,
        tolerance=0.0,
    )

    assert result["promoted"] is True
    assert result["previous_version"] == "v1"


def test_rollback_restores_previous_version(tmp_path):
    first = write_csv(tmp_path, synthetic_frame())
    retrain(output_dir=tmp_path / "models", data_path=first, version="v1")
    shuffled = synthetic_frame()
    shuffled["sold_price"] = shuffled["sold_price"].sample(frac=1.0, random_state=1).to_numpy() * 5
    retrain(output_dir=tmp_path / "models", data_path=write_csv(tmp_path, shuffled), version="v2", force=True)

    result = rollback(output_dir=tmp_path / "models")

    assert result == {"promoted": "v1", "rolled_back_from": "v2"}
    with SessionLocal() as session:
        promoted = session.query(ModelVersion).filter(ModelVersion.promoted.is_(True)).all()
    assert [row.version for row in promoted] == ["v1"]


def test_retrain_requires_minimum_rows(tmp_path):
    data = write_csv(tmp_path, synthetic_frame(rows=5))
    with pytest.raises(ValueError, match="at least"):
        retrain(output_dir=tmp_path / "models", data_path=data, min_rows=20)


def test_synthetic_frame_matches_feature_contract():
    frame = synthetic_frame(rows=10)
    assert set(FEATURE_COLUMNS).issubset(frame.columns)
