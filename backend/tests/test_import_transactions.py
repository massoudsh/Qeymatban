from pathlib import Path

import pandas as pd
import pytest

from app.scripts.import_transactions import normalize_transactions


def valid_row() -> dict:
    return {
        "area_sqm": 92,
        "year_built": 1397,
        "floor": 3,
        "total_floors": 6,
        "rooms": 2,
        "has_parking": True,
        "has_elevator": True,
        "has_storage": False,
        "renovated": False,
        "light_score": 4,
        "view_score": 3,
        "access_score": 5,
        "sold_price": 12_000_000_000,
    }


def test_normalize_transactions_adds_id(tmp_path: Path):
    source, destination = tmp_path / "source.csv", tmp_path / "clean.csv"
    pd.DataFrame([valid_row()]).to_csv(source, index=False)

    assert normalize_transactions(source, destination) == 1
    assert pd.read_csv(destination)["id"].notna().all()


def test_normalize_transactions_rejects_invalid_scores(tmp_path: Path):
    source = tmp_path / "source.csv"
    row = valid_row()
    row["light_score"] = 7
    pd.DataFrame([row]).to_csv(source, index=False)

    with pytest.raises(ValueError, match="light_score"):
        normalize_transactions(source, tmp_path / "clean.csv")
