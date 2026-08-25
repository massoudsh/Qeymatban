import pandas as pd

from app.ml.comparables import ComparablesFinder
from app.ml.pricing_pipeline import FEATURE_COLUMNS


def test_comparables_supports_less_than_five_training_rows():
    rows = []
    for index in range(3):
        rows.append(
            {
                "id": f"property-{index}",
                "area_sqm": 80 + index,
                "year_built": 1395,
                "floor": 2,
                "total_floors": 5,
                "rooms": 2,
                "has_parking": True,
                "has_elevator": True,
                "has_storage": True,
                "renovated": False,
                "light_score": 4,
                "view_score": 3,
                "access_score": 4,
            }
        )
    frame = pd.DataFrame(rows)
    finder = ComparablesFinder(n_neighbors=5)
    finder.fit(frame)

    result = finder.find(frame.iloc[[0]][FEATURE_COLUMNS])[0]

    assert len(result) == 3
    assert result[0]["id"] == "property-0"
    assert result[0]["similarity"] == 1.0
