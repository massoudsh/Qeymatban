"""Load validated transaction CSVs into the ``properties`` and ``transactions`` tables.

Run after ``import_transactions`` has normalized and validated the source. Each
row becomes one property plus one transaction, which is the shape the retrain
job and the comparables finder expect.

    python -m app.scripts.load_database data/transactions.csv
"""

from __future__ import annotations

import argparse
import json
import uuid
from pathlib import Path

import pandas as pd
from sqlalchemy import select

from app.db import IS_POSTGRES, Property, SessionLocal, Transaction, create_tables, upgrade_postgres_schema
from app.ml.dataset import backfill_embeddings, compute_embedding, parse_sold_date
from app.ml.pricing_pipeline import FEATURE_COLUMNS


def _as_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y", "بله"}


def load_transactions(
    source: Path,
    neighborhood: str = "نامشخص",
    city: str = "تهران",
    batch_size: int = 500,
) -> dict[str, int]:
    """Insert properties and transactions, skipping rows already present by id.

    The CSV ``id`` column becomes the transaction id, so re-running the same
    export is a no-op rather than a duplicate load.
    """
    frame = pd.read_csv(source)
    missing = sorted({"sold_price", *FEATURE_COLUMNS} - set(frame.columns))
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")

    create_tables()
    if IS_POSTGRES:
        upgrade_postgres_schema()

    inserted_transactions = 0
    inserted_properties = 0
    skipped = 0

    with SessionLocal() as session:
        existing_ids = {str(row) for row in session.scalars(select(Transaction.id))}
        pending: list[tuple[Property, Transaction]] = []

        for _, row in frame.iterrows():
            transaction_id = str(row["id"]) if "id" in frame.columns else str(uuid.uuid4())
            if transaction_id in existing_ids:
                skipped += 1
                continue

            features = {column: row[column] for column in FEATURE_COLUMNS}
            property_record = Property(
                title=f"معامله {transaction_id[:8]}",
                neighborhood=str(row.get("neighborhood") or neighborhood),
                city=str(row.get("city") or city),
                area_sqm=float(row["area_sqm"]),
                year_built=int(row["year_built"]),
                floor=int(row["floor"]),
                total_floors=int(row["total_floors"]),
                rooms=int(row["rooms"]),
                has_parking=_as_bool(row["has_parking"]),
                has_elevator=_as_bool(row["has_elevator"]),
                has_storage=_as_bool(row["has_storage"]),
                renovated=_as_bool(row["renovated"]),
                light_score=int(row["light_score"]),
                view_score=int(row["view_score"]),
                access_score=int(row["access_score"]),
                status="sold",
                feature_embedding=compute_embedding(
                    {key: float(value) for key, value in features.items()}
                ),
            )
            sold_date = row["sold_date"] if "sold_date" in frame.columns else None
            if sold_date is None or pd.isna(sold_date):
                raise ValueError(f"Row {transaction_id} has no sold_date; it is required for the transactions table")
            transaction = Transaction(
                id=transaction_id,
                sold_price=float(row["sold_price"]),
                sold_date=parse_sold_date(sold_date),
                source=str(row["source"]) if "source" in frame.columns and not pd.isna(row["source"]) else "import",
            )
            property_record.transactions.append(transaction)
            pending.append((property_record, transaction))
            existing_ids.add(transaction_id)

            if len(pending) >= batch_size:
                session.add_all([prop for prop, _ in pending])
                session.commit()
                inserted_properties += len(pending)
                inserted_transactions += len(pending)
                pending = []

        if pending:
            session.add_all([prop for prop, _ in pending])
            session.commit()
            inserted_properties += len(pending)
            inserted_transactions += len(pending)

    backfill_embeddings()
    return {
        "transactions": inserted_transactions,
        "properties": inserted_properties,
        "skipped": skipped,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--neighborhood", default="نامشخص")
    parser.add_argument("--city", default="تهران")
    args = parser.parse_args()
    summary = load_transactions(args.source, neighborhood=args.neighborhood, city=args.city)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
