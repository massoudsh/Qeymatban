import pandas as pd
import pytest

from app.ml.pricing_pipeline import FEATURE_COLUMNS
from app.scripts.import_transactions import normalize_transactions


def valid_frame() -> pd.DataFrame:
    row = {column: 1 for column in FEATURE_COLUMNS}
    row.update({"area_sqm": 92, "year_built": 1397, "sold_price": 100_000_000})
    return pd.DataFrame([row])


def test_normalize_transactions_writes_valid_training_schema(tmp_path):
    source = tmp_path / "raw.csv"
    destination = tmp_path / "transactions.csv"
    valid_frame().to_csv(source, index=False)

    rows = normalize_transactions(source, destination)
    output = pd.read_csv(destination)

    assert rows == 1
    assert "id" in output.columns
    assert output.loc[0, "sold_price"] == 100_000_000


def test_normalize_transactions_rejects_invalid_scores(tmp_path):
    source = tmp_path / "raw.csv"
    destination = tmp_path / "transactions.csv"
    frame = valid_frame()
    frame.loc[0, "light_score"] = 6
    frame.to_csv(source, index=False)

    with pytest.raises(ValueError, match="light_score"):
        normalize_transactions(source, destination)
