"""Retrain the valuation model, record its metrics, and promote it only if it is not worse.

Designed to be run from cron (or any scheduler); it is idempotent and never
replaces the current artifact with a regression.

    python -m app.scripts.retrain                 # train from the transactions table
    python -m app.scripts.retrain --force         # promote even if metrics regress
    python -m app.scripts.retrain --rollback      # re-promote the previous version
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error
from sqlalchemy import select

from app.db import ModelVersion, SessionLocal, create_tables
from app.ml.dataset import training_frame_from_db
from app.ml.pricing_pipeline import FEATURE_COLUMNS, MODEL_FAMILIES
from app.ml.valuation_service import ValuationService

# A candidate may be this much worse before it is rejected. Small enough to catch
# real regressions, large enough to absorb run-to-run noise in a small dataset.
DEFAULT_TOLERANCE = 0.02


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _current_promoted() -> ModelVersion | None:
    with SessionLocal() as session:
        return session.scalars(
            select(ModelVersion).where(ModelVersion.promoted.is_(True)).order_by(ModelVersion.trained_at.desc())
        ).first()


def _record(entry: ModelVersion, promoted: bool, notes: str) -> ModelVersion:
    with SessionLocal() as session:
        if promoted:
            for existing in session.scalars(select(ModelVersion).where(ModelVersion.promoted.is_(True))).all():
                existing.promoted = False
        session.merge(
            ModelVersion(
                version=entry.version,
                model_family=entry.model_family,
                artifact_path=entry.artifact_path,
                trained_at=entry.trained_at,
                training_rows=entry.training_rows,
                validation_rows=entry.validation_rows,
                mae=entry.mae,
                mape=entry.mape,
                dataset_sha256=entry.dataset_sha256,
                data_source=entry.data_source,
                promoted=promoted,
                notes=notes,
            )
        )
        session.commit()
    return entry


def _train_candidate(frame: pd.DataFrame, output_dir: Path, version: str, model_family: str) -> tuple[ValuationService, dict]:
    if "sold_date" in frame:
        frame = frame.sort_values("sold_date")
    split = max(1, int(len(frame) * 0.8))
    train_frame, validation_frame = frame.iloc[:split], frame.iloc[split:]
    if validation_frame.empty:
        raise ValueError("Validation set is empty; import more transactions")

    service = ValuationService(model_version=version, model_family=model_family)
    service.fit(train_frame)
    predictions = service.pricing_model.predict(validation_frame)
    metrics = {
        "model_version": version,
        "model_family": model_family,
        "trained_at": datetime.now(UTC).isoformat(),
        "training_rows": len(train_frame),
        "validation_rows": len(validation_frame),
        "mae": float(mean_absolute_error(validation_frame["sold_price"], predictions)),
        "mape": float(mean_absolute_percentage_error(validation_frame["sold_price"], predictions)),
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = output_dir / f"valuation-{version}.joblib"
    service.save(artifact_path)
    (output_dir / f"valuation-{version}.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    return service, {**metrics, "artifact": str(artifact_path)}


def retrain(
    output_dir: Path = Path("models"),
    version: str | None = None,
    model_family: str = "xgboost",
    data_path: Path | None = None,
    force: bool = False,
    tolerance: float = DEFAULT_TOLERANCE,
    min_rows: int = 20,
) -> dict[str, object]:
    if model_family not in MODEL_FAMILIES:
        raise ValueError(f"Unsupported model family: {model_family}")

    create_tables()
    if data_path is not None:
        frame = pd.read_csv(data_path)
        missing = sorted({"sold_price", *FEATURE_COLUMNS} - set(frame.columns))
        if missing:
            raise ValueError(f"Missing training columns: {', '.join(missing)}")
        dataset_sha = _sha256(data_path)
        data_source = str(data_path)
    else:
        frame = training_frame_from_db(min_rows=min_rows)
        dataset_sha = hashlib.sha256(frame.to_csv(index=False).encode("utf-8")).hexdigest()
        data_source = "transactions table"

    if len(frame) < min_rows:
        raise ValueError(f"Need at least {min_rows} rows, found {len(frame)}")

    version = version or datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    _, metrics = _train_candidate(frame, output_dir, version, model_family)

    current = _current_promoted()
    candidate_mape = float(metrics["mape"])
    if current is None:
        promoted, decision = True, "no promoted version yet"
    elif force:
        promoted, decision = True, "forced promotion"
    elif current.mape is None:
        promoted, decision = True, "current version has no recorded metric"
    elif candidate_mape <= float(current.mape) * (1 + tolerance):
        promoted, decision = True, "candidate not worse than current"
    else:
        promoted, decision = False, (
            f"rejected: MAPE {candidate_mape:.4f} worse than {current.version} at {float(current.mape):.4f}"
        )

    entry = ModelVersion(
        version=version,
        model_family=model_family,
        artifact_path=str(metrics["artifact"]),
        trained_at=datetime.now(UTC).replace(tzinfo=None),
        training_rows=int(metrics["training_rows"]),
        validation_rows=int(metrics["validation_rows"]),
        mae=float(metrics["mae"]),
        mape=candidate_mape,
        dataset_sha256=dataset_sha,
        data_source=data_source,
        promoted=promoted,
        notes=decision,
    )
    _record(entry, promoted, decision)

    if promoted:
        shutil.copyfile(metrics["artifact"], output_dir / "current.joblib")
        (output_dir / "current.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")

    return {**metrics, "promoted": promoted, "decision": decision, "previous_version": current.version if current else None}


def rollback(output_dir: Path = Path("models")) -> dict[str, object]:
    """Re-promote the most recent version other than the current one."""
    with SessionLocal() as session:
        rows = session.scalars(select(ModelVersion).order_by(ModelVersion.trained_at.desc())).all()
        current = next((row for row in rows if row.promoted), None)
        previous = next((row for row in rows if current is None or row.version != current.version), None)
        if previous is None:
            raise ValueError("No other model version is available to roll back to")
        for row in rows:
            row.promoted = row.version == previous.version
        session.commit()
        # Copy before the session closes; ORM attributes expire on commit.
        previous_version = previous.version
        previous_artifact = Path(previous.artifact_path)
        current_version = current.version if current else None

    if not previous_artifact.is_file():
        raise FileNotFoundError(f"Artifact for {previous_version} is missing: {previous_artifact}")
    shutil.copyfile(previous_artifact, output_dir / "current.joblib")
    return {"promoted": previous_version, "rolled_back_from": current_version}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("models"))
    parser.add_argument("--version")
    parser.add_argument("--model-family", choices=MODEL_FAMILIES, default="xgboost")
    parser.add_argument("--data", type=Path, help="CSV instead of the transactions table")
    parser.add_argument("--force", action="store_true", help="Promote even if metrics regress")
    parser.add_argument("--tolerance", type=float, default=DEFAULT_TOLERANCE)
    parser.add_argument("--min-rows", type=int, default=20)
    parser.add_argument("--rollback", action="store_true", help="Re-promote the previous version and exit")
    args = parser.parse_args()

    if args.rollback:
        print(json.dumps(rollback(args.output_dir), ensure_ascii=False, indent=2))
        return
    print(
        json.dumps(
            retrain(
                output_dir=args.output_dir,
                version=args.version,
                model_family=args.model_family,
                data_path=args.data,
                force=args.force,
                tolerance=args.tolerance,
                min_rows=args.min_rows,
            ),
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
