"""Golden-dataset evaluation: metrics and threshold enforcement."""

import pandas as pd
import pytest

from app.ml.valuation_service import ValuationService
from app.scripts.evaluate import evaluate


def training_frame(rows: int = 60) -> pd.DataFrame:
    records = []
    for index in range(rows):
        area = 70 + index % 80
        record = {
            "id": f"eval-{index:04d}",
            "area_sqm": area,
            "year_built": 1385 + index % 18,
            "floor": index % 7,
            "total_floors": 8,
            "rooms": 1 + area // 40,
            "has_parking": index % 2 == 0,
            "has_elevator": index % 3 != 0,
            "has_storage": index % 4 != 0,
            "renovated": index % 5 == 0,
            "light_score": 1 + index % 5,
            "view_score": 1 + (index + 1) % 5,
            "access_score": 1 + (index + 2) % 5,
        }
        record["sold_price"] = float(area * 85_000_000 + record["floor"] * 90_000_000)
        records.append(record)
    return pd.DataFrame(records)


@pytest.fixture()
def trained_model(tmp_path):
    service = ValuationService(model_version="eval-test")
    service.fit(training_frame())
    path = tmp_path / "model.joblib"
    service.save(path)
    return path


def test_evaluate_reports_metrics(trained_model, tmp_path):
    golden = tmp_path / "golden.csv"
    training_frame(rows=20).to_csv(golden, index=False)

    result = evaluate(trained_model, golden)

    assert result["model_version"] == "eval-test"
    assert result["cases"] == 20
    assert result["mae"] >= 0
    assert 0 <= result["within_15_percent"] <= 1


def test_evaluate_rejects_missing_columns(trained_model, tmp_path):
    golden = tmp_path / "golden.csv"
    training_frame(rows=5).drop(columns=["sold_price"]).to_csv(golden, index=False)

    with pytest.raises(ValueError, match="sold_price"):
        evaluate(trained_model, golden)


def test_evaluate_rejects_empty_dataset(trained_model, tmp_path):
    golden = tmp_path / "golden.csv"

    # Write the header explicitly; pandas emits nothing at all for a zero-row frame.
    golden.write_text(",".join(training_frame(rows=1).columns) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="empty"):
        evaluate(trained_model, golden)
