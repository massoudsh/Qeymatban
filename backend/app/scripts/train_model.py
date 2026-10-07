"""Train and version a valuation artifact from canonical transaction data."""

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error

from app.ml.pricing_pipeline import FEATURE_COLUMNS, MODEL_FAMILIES
from app.ml.valuation_service import ValuationService


def train(
    data_path: Path,
    output_dir: Path,
    version: str | None = None,
    model_family: str = "xgboost",
) -> dict[str, object]:
    frame = pd.read_csv(data_path)
    required = {"id", "sold_price", *FEATURE_COLUMNS}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"Missing training columns: {', '.join(missing)}")
    if len(frame) < 20:
        raise ValueError("At least 20 validated transactions are required")

    if "sold_date" in frame:
        frame = frame.sort_values("sold_date")
    split = max(1, int(len(frame) * 0.8))
    train_frame, validation_frame = frame.iloc[:split], frame.iloc[split:]
    if validation_frame.empty:
        raise ValueError("Validation set is empty")

    if model_family not in MODEL_FAMILIES:
        raise ValueError(f"Unsupported model family: {model_family}")
    model_version = version or datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    service = ValuationService(model_version=model_version, model_family=model_family)
    service.fit(train_frame)

    predictions = service.pricing_model.predict(validation_frame)
    metrics = {
        "model_version": model_version,
        "model_family": model_family,
        "trained_at": datetime.now(UTC).isoformat(),
        "training_rows": len(train_frame),
        "validation_rows": len(validation_frame),
        "mae": float(mean_absolute_error(validation_frame["sold_price"], predictions)),
        "mape": float(mean_absolute_percentage_error(validation_frame["sold_price"], predictions)),
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = output_dir / f"valuation-{model_version}.joblib"
    service.save(artifact_path)
    (output_dir / f"valuation-{model_version}.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return {**metrics, "artifact": str(artifact_path)}


def model_family_from_benchmark(path: Path) -> str:
    payload = json.loads(path.read_text(encoding="utf-8"))
    model_family = payload.get("model_family")
    if model_family not in MODEL_FAMILIES:
        raise ValueError(f"Benchmark winner must be one of: {', '.join(MODEL_FAMILIES)}")
    return model_family


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("models"))
    parser.add_argument("--version")
    parser.add_argument("--model-family", choices=MODEL_FAMILIES, default="xgboost")
    parser.add_argument("--benchmark-winner", type=Path)
    args = parser.parse_args()
    model_family = model_family_from_benchmark(args.benchmark_winner) if args.benchmark_winner else args.model_family
    print(json.dumps(train(args.data, args.output_dir, args.version, model_family), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
