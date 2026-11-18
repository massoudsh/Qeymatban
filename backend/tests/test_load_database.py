"""Database import: properties, transactions and feature embeddings."""

import pandas as pd
import pytest

from app.db import Base, ModelVersion, Property, SessionLocal, Transaction, engine
from app.ml.dataset import backfill_embeddings, compute_embedding, training_frame_from_db
from app.ml.pricing_pipeline import FEATURE_COLUMNS
from app.scripts.load_database import load_transactions


def csv_frame(rows: int = 4) -> pd.DataFrame:
    records = []
    for index in range(rows):
        records.append(
            {
                "id": f"import-{index}",
                "neighborhood": "پونک",
                "city": "تهران",
                "sold_date": f"2024-0{1 + index}-15",
                "source": "partner-export",
                "area_sqm": 80 + index,
                "year_built": 1395,
                "floor": 2,
                "total_floors": 6,
                "rooms": 2,
                "has_parking": True,
                "has_elevator": True,
                "has_storage": False,
                "renovated": False,
                "light_score": 4,
                "view_score": 3,
                "access_score": 4,
                "sold_price": 12_000_000_000 + index * 100_000_000,
            }
        )
    return pd.DataFrame(records)


def setup_function():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def test_load_transactions_creates_properties_and_transactions(tmp_path):
    source = tmp_path / "validated.csv"
    csv_frame().to_csv(source, index=False)

    summary = load_transactions(source)

    assert summary == {"transactions": 4, "properties": 4, "skipped": 0}
    with SessionLocal() as session:
        assert session.query(Transaction).count() == 4
        properties = session.query(Property).all()
    assert {prop.neighborhood for prop in properties} == {"پونک"}
    assert all(prop.feature_embedding for prop in properties)


def test_load_transactions_is_idempotent(tmp_path):
    source = tmp_path / "validated.csv"
    csv_frame().to_csv(source, index=False)
    load_transactions(source)

    summary = load_transactions(source)

    assert summary == {"transactions": 0, "properties": 0, "skipped": 4}
    with SessionLocal() as session:
        assert session.query(Transaction).count() == 4


def test_load_transactions_requires_sold_date(tmp_path):
    frame = csv_frame().drop(columns=["sold_date"])
    source = tmp_path / "validated.csv"
    frame.to_csv(source, index=False)

    with pytest.raises(ValueError, match="sold_date"):
        load_transactions(source)


def test_training_frame_joins_property_features(tmp_path):
    source = tmp_path / "validated.csv"
    csv_frame(rows=3).to_csv(source, index=False)
    load_transactions(source)

    frame = training_frame_from_db(min_rows=3)

    assert len(frame) == 3
    assert {"id", "neighborhood", "sold_date", "sold_price", *FEATURE_COLUMNS}.issubset(frame.columns)
    assert frame["neighborhood"].eq("پونک").all()


def test_training_frame_rejects_empty_database():
    with pytest.raises(ValueError, match="No transactions"):
        training_frame_from_db()


def test_embeddings_are_unit_length_and_backfilled():
    vector = compute_embedding({column: 1 for column in FEATURE_COLUMNS})
    norm = sum(value**2 for value in vector) ** 0.5
    assert norm == pytest.approx(1.0)

    with SessionLocal() as session:
        session.add(
            Property(
                title="بدون بردار",
                neighborhood="پونک",
                city="تهران",
                area_sqm=100,
                year_built=1398,
                floor=3,
                total_floors=6,
                rooms=2,
                light_score=4,
                view_score=3,
                access_score=4,
            )
        )
        session.commit()

    assert backfill_embeddings() == 1
    with SessionLocal() as session:
        assert session.query(Property).one().feature_embedding


def test_model_version_table_exists():
    with SessionLocal() as session:
        assert session.query(ModelVersion).count() == 0
