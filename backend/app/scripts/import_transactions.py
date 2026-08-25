"""Normalize a partner transaction export into Qeymatban's training schema."""

import argparse
import uuid
from pathlib import Path

import pandas as pd

from app.ml.pricing_pipeline import FEATURE_COLUMNS

REQUIRED_COLUMNS = [*FEATURE_COLUMNS, "sold_price"]
OPTIONAL_COLUMNS = ["id", "sold_date", "source"]


def normalize_transactions(source: Path, destination: Path) -> int:
    frame = pd.read_csv(source)
    missing = sorted(set(REQUIRED_COLUMNS) - set(frame.columns))
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")

    output = frame[[column for column in [*OPTIONAL_COLUMNS, *REQUIRED_COLUMNS] if column in frame]].copy()
    if "id" not in output:
        output.insert(0, "id", [str(uuid.uuid4()) for _ in range(len(output))])
    if output["id"].astype(str).duplicated().any():
        raise ValueError("Transaction ids must be unique")
    if output[REQUIRED_COLUMNS].isna().any().any():
        raise ValueError("Required training values cannot be empty")
    if (output["area_sqm"] <= 0).any() or (output["sold_price"] <= 0).any():
        raise ValueError("area_sqm and sold_price must be positive")
    for score in ("light_score", "view_score", "access_score"):
        if not output[score].between(1, 5).all():
            raise ValueError(f"{score} must be between 1 and 5")

    destination.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(destination, index=False)
    return len(output)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    rows = normalize_transactions(args.source, args.destination)
    print(f"Imported {rows} validated transactions into {args.destination}")


if __name__ == "__main__":
    main()
