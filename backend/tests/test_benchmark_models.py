import pandas as pd

from app.ml.pricing_pipeline import FEATURE_COLUMNS
from app.scripts.benchmark_models import NEIGHBORHOODS, generate_mock_transactions


def test_mock_transactions_are_reproducible_and_complete():
    first = generate_mock_transactions(rows=120, seed=7)
    second = generate_mock_transactions(rows=120, seed=7)

    pd.testing.assert_frame_equal(first, second)
    assert {"id", "sold_date", "neighborhood", "sold_price", *FEATURE_COLUMNS} <= set(first.columns)
    assert first["sold_price"].gt(0).all()
    assert set(first["neighborhood"]).issubset(NEIGHBORHOODS)
    assert first["neighborhood"].nunique() > 1
