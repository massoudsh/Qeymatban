"""Regression scoring for the valuation engine against a golden dataset.

The benchmark script compares model families; this script answers a different
question: did the artifact currently in production get worse on a fixed set of
cases that matter to the business? It exits non-zero when a threshold is missed,
so CI or cron can block a rollout.

    python -m app.scripts.evaluate --model models/current.joblib --data golden.csv
    python -m app.scripts.evaluate --model models/current.joblib --data golden.csv --max-mape 0.20
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error, median_absolute_error

from app.ml.pricing_pipeline import FEATURE_COLUMNS
from app.ml.valuation_service import ValuationService

# Business-facing quality bars. A valuation is "usable" when the mid estimate is
# within this share of the actual sale price.
DEFAULT_MAX_MAPE = 0.25
DEFAULT_MAX_MAE_RATIO = 0.30


def evaluate(model_path: Path, data_path: Path) -> dict[str, object]:
    frame = pd.read_csv(data_path)
    missing = sorted({*FEATURE_COLUMNS, "sold_price"} - set(frame.columns))
    if missing:
        raise ValueError(f"Missing evaluation columns: {', '.join(missing)}")
    if frame.empty:
        raise ValueError("Golden dataset is empty")

    service = ValuationService.load(model_path)
    predictions = np.maximum(1.0, service.pricing_model.predict(frame))
    actual = frame["sold_price"].to_numpy()

    mae = float(mean_absolute_error(actual, predictions))
    mape = float(mean_absolute_percentage_error(actual, predictions))
    median_ae = float(median_absolute_error(actual, predictions))
    # Share of cases whose error is within 15% of the actual price.
    within_15pct = float(np.mean(np.abs(predictions - actual) / actual <= 0.15))

    return {
        "model_version": service.model_version,
        "model_family": service.model_family,
        "cases": len(frame),
        "mae": mae,
        "mape": mape,
        "median_absolute_error": median_ae,
        "within_15_percent": within_15pct,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--data", type=Path, required=True, help="Golden dataset CSV with sold_price")
    parser.add_argument("--max-mape", type=float, default=DEFAULT_MAX_MAPE)
    parser.add_argument("--max-mae-ratio", type=float, default=DEFAULT_MAX_MAE_RATIO)
    args = parser.parse_args()

    result = evaluate(args.model, args.data)
    mean_price = float(pd.read_csv(args.data)["sold_price"].mean())
    mae_ratio = result["mae"] / mean_price if mean_price else float("inf")

    failures = []
    if result["mape"] > args.max_mape:
        failures.append(f"MAPE {result['mape']:.4f} > {args.max_mape}")
    if mae_ratio > args.max_mae_ratio:
        failures.append(f"MAE/mean price {mae_ratio:.4f} > {args.max_mae_ratio}")

    print(json.dumps({**result, "mae_ratio": mae_ratio, "failures": failures}, ensure_ascii=False, indent=2))
    if failures:
        sys.exit(1)


if __name__ == "__main__":
    main()
