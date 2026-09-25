import pandas as pd

from app.ml.comparables import ComparablesFinder
from app.ml.pricing_pipeline import FEATURE_COLUMNS


def frame_with_rows(rows: int) -> pd.DataFrame:
    data = []
    for index in range(rows):
        row = {column: 1 for column in FEATURE_COLUMNS}
        row.update({"id": f"property-{index}", "area_sqm": 80 + index, "year_built": 1395 + index})
        data.append(row)
    return pd.DataFrame(data)


def test_comparables_limits_neighbors_to_available_rows():
    frame = frame_with_rows(2)
    finder = ComparablesFinder(n_neighbors=5)

    finder.fit(frame)
    result = finder.find(frame.iloc[[0]])

    assert len(result) == 1
    assert len(result[0]) == 2
    assert {item["id"] for item in result[0]} == {"property-0", "property-1"}
