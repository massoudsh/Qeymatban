"""Load canonical training rows from the database and maintain feature embeddings.

The valuation engine trains on ``FEATURE_COLUMNS`` plus ``sold_price``, keyed by
``neighborhood`` and ``sold_date`` for the temporal and neighborhood splits.
Those columns live across ``properties`` and ``transactions``, so this module is
the single place that joins them into the frame the model expects.
"""

from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd
from sqlalchemy import select

from app.db import Property, SessionLocal, Transaction

# Features are normalized to a unit vector so cosine distance behaves like the
# in-process comparables finder.
EMBEDDING_DIMENSIONS = 12


def training_frame_from_db(min_rows: int = 0) -> pd.DataFrame:
    """Return one row per transaction joined with its property attributes.

    Columns: ``id`` (transaction id), ``property_id``, ``neighborhood``, ``city``,
    ``sold_date``, ``sold_price``, ``source`` and every model feature.
    """
    from app.ml.pricing_pipeline import FEATURE_COLUMNS

    with SessionLocal() as session:
        rows = session.execute(
            select(Transaction, Property).join(Property, Transaction.property_id == Property.id)
        ).all()

    records: list[dict[str, object]] = []
    for transaction, property_record in rows:
        record: dict[str, object] = {
            "id": str(transaction.id),
            "property_id": str(property_record.id),
            "neighborhood": property_record.neighborhood,
            "city": property_record.city,
            "sold_date": transaction.sold_date.isoformat(),
            "sold_price": float(transaction.sold_price),
            "source": transaction.source or "database",
        }
        for column in FEATURE_COLUMNS:
            record[column] = getattr(property_record, column)
        records.append(record)

    frame = pd.DataFrame(records)
    if frame.empty:
        raise ValueError("No transactions in the database; import data before training")
    if len(frame) < min_rows:
        raise ValueError(f"Need at least {min_rows} transactions, found {len(frame)}")
    return frame


def compute_embedding(features: dict[str, float], baseline: dict[str, float] | None = None) -> list[float]:
    """Deterministic, dependency-light feature vector for comparable search.

    Values are divided by a reference scale so no single large column (area in
    square metres) dominates the cosine distance, then L2-normalized.
    """
    from app.ml.pricing_pipeline import FEATURE_COLUMNS

    reference = baseline or DEFAULT_BASELINE
    vector = np.array(
        [float(features.get(column, 0.0)) / reference.get(column, 1.0) for column in FEATURE_COLUMNS],
        dtype=float,
    )
    norm = float(np.linalg.norm(vector))
    if norm == 0.0:
        return [0.0] * len(vector)
    return [float(value) for value in vector / norm]


# Typical Tehran apartment values; only the ratios matter for cosine distance.
DEFAULT_BASELINE: dict[str, float] = {
    "area_sqm": 120.0,
    "year_built": 1400.0,
    "floor": 5.0,
    "total_floors": 6.0,
    "rooms": 3.0,
    "has_parking": 1.0,
    "has_elevator": 1.0,
    "has_storage": 1.0,
    "renovated": 1.0,
    "light_score": 5.0,
    "view_score": 5.0,
    "access_score": 5.0,
}


def backfill_embeddings() -> int:
    """Compute ``feature_embedding`` for properties that do not have one yet."""
    from app.ml.pricing_pipeline import FEATURE_COLUMNS

    updated = 0
    with SessionLocal() as session:
        pending = session.scalars(select(Property).where(Property.feature_embedding.is_(None))).all()
        for property_record in pending:
            features = {column: float(getattr(property_record, column)) for column in FEATURE_COLUMNS}
            property_record.feature_embedding = compute_embedding(features)
            updated += 1
        session.commit()
    return updated


def parse_sold_date(value: str | date) -> date:
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])
