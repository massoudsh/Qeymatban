"""Benchmark tabular valuation models on deterministic synthetic property transactions."""

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error
from sklearn.model_selection import GroupShuffleSplit

from app.ml.pricing_pipeline import FEATURE_COLUMNS, MODEL_FAMILIES, create_regressor


@dataclass(frozen=True)
class BenchmarkResult:
    model_family: str
    temporal_mae: float | None
    temporal_mape: float | None
    neighborhood_mae: float | None
    neighborhood_mape: float | None
    score: float | None
    status: str


NEIGHBORHOODS = {
    "نیاوران": 180_000_000,
    "فرمانیه": 160_000_000,
    "سعادت‌آباد": 130_000_000,
    "پونک": 95_000_000,
    "تهرانپارس": 78_000_000,
    "چیتگر": 88_000_000,
}


def generate_mock_transactions(rows: int = 2400, seed: int = 42) -> pd.DataFrame:
    """Generate reproducible, plausible Tehran sale transactions for pipeline validation only."""
    if rows < len(NEIGHBORHOODS) * 10:
        raise ValueError(f"rows must be at least {len(NEIGHBORHOODS) * 10}")

    rng = np.random.default_rng(seed)
    names = np.array(list(NEIGHBORHOODS))
    neighborhood = rng.choice(names, size=rows, p=[0.13, 0.12, 0.21, 0.18, 0.19, 0.17])
    sold_date = pd.Timestamp("2021-01-01") + pd.to_timedelta(rng.integers(0, 1461, size=rows), unit="D")
    area = np.clip(rng.lognormal(mean=4.72, sigma=0.31, size=rows), 45, 330).round(1)
    year_built = rng.integers(1375, 1404, size=rows)
    total_floors = rng.integers(3, 13, size=rows)
    floor = np.array([rng.integers(0, upper) for upper in total_floors])
    rooms = np.clip(np.floor(area / 52).astype(int), 1, 5)
    parking = rng.random(rows) < 0.78
    elevator = (total_floors >= 5) | (rng.random(rows) < 0.45)
    storage = rng.random(rows) < 0.68
    renovated = (1403 - year_built > 12) & (rng.random(rows) < 0.34)
    light = rng.integers(1, 6, size=rows)
    view = rng.integers(1, 6, size=rows)
    access = rng.integers(1, 6, size=rows)

    base_per_sqm = np.array([NEIGHBORHOODS[item] for item in neighborhood], dtype=float)
    months_since_start = ((sold_date - pd.Timestamp("2021-01-01")).days.to_numpy() / 30.44)
    age_discount = 1 - np.clip((1403 - year_built) * 0.007, 0, 0.22)
    floor_factor = 1 + np.minimum(floor, 8) * 0.008
    amenities_factor = 1 + parking * 0.045 + elevator * 0.035 + storage * 0.02 + renovated * 0.075
    quality_factor = 1 + (light - 3) * 0.018 + (view - 3) * 0.016 + (access - 3) * 0.02
    market_factor = 1 + months_since_start * 0.009
    noise = rng.lognormal(mean=0, sigma=0.07, size=rows)
    sold_price = (area * base_per_sqm * age_discount * floor_factor * amenities_factor * quality_factor * market_factor * noise).round(-5)

    return pd.DataFrame(
        {
            "id": [f"mock-{seed}-{index:05d}" for index in range(rows)],
            "neighborhood": neighborhood,
            "city": "تهران",
            "sold_date": sold_date.date.astype(str),
            "source": "synthetic-benchmark",
            "area_sqm": area,
            "year_built": year_built,
            "floor": floor,
            "total_floors": total_floors,
            "rooms": rooms,
            "has_parking": parking,
            "has_elevator": elevator,
            "has_storage": storage,
            "renovated": renovated,
            "light_score": light,
            "view_score": view,
            "access_score": access,
            "sold_price": sold_price,
        }
    )


def _metrics(model, train_frame: pd.DataFrame, test_frame: pd.DataFrame) -> tuple[float, float]:
    model.fit(train_frame[FEATURE_COLUMNS], train_frame["sold_price"])
    prediction = np.maximum(1, np.asarray(model.predict(test_frame[FEATURE_COLUMNS])))
    return (
        float(mean_absolute_error(test_frame["sold_price"], prediction)),
        float(mean_absolute_percentage_error(test_frame["sold_price"], prediction)),
    )


def benchmark(frame: pd.DataFrame) -> list[BenchmarkResult]:
    ordered = frame.assign(sold_date=pd.to_datetime(frame["sold_date"])).sort_values("sold_date")
    cutoff = ordered["sold_date"].quantile(0.8)
    time_train = ordered.loc[ordered["sold_date"] < cutoff]
    time_test = ordered.loc[ordered["sold_date"] >= cutoff]
    group_split = GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=42)
    neighborhood_train_index, neighborhood_test_index = next(group_split.split(ordered, groups=ordered["neighborhood"]))
    neighborhood_train = ordered.iloc[neighborhood_train_index]
    neighborhood_test = ordered.iloc[neighborhood_test_index]

    results: list[BenchmarkResult] = []
    for model_family in MODEL_FAMILIES:
        try:
            temporal_mae, temporal_mape = _metrics(create_regressor(model_family), time_train, time_test)
            neighborhood_mae, neighborhood_mape = _metrics(create_regressor(model_family), neighborhood_train, neighborhood_test)
            results.append(
                BenchmarkResult(
                    model_family=model_family,
                    temporal_mae=temporal_mae,
                    temporal_mape=temporal_mape,
                    neighborhood_mae=neighborhood_mae,
                    neighborhood_mape=neighborhood_mape,
                    score=(temporal_mape + neighborhood_mape) / 2,
                    status="ok",
                )
            )
        except ImportError as error:
            results.append(BenchmarkResult(model_family, None, None, None, None, None, f"unavailable: {error.name}"))
    return results


def run(rows: int, seed: int, output_dir: Path) -> dict[str, object]:
    frame = generate_mock_transactions(rows=rows, seed=seed)
    output_dir.mkdir(parents=True, exist_ok=True)
    data_path = output_dir / "mock-transactions.csv"
    frame.to_csv(data_path, index=False)
    results = benchmark(frame)
    eligible = [item for item in results if item.status == "ok"]
    if not eligible:
        raise RuntimeError("No benchmark model is installed")
    winner = min(eligible, key=lambda item: item.score if item.score is not None else float("inf"))
    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "seed": seed,
        "rows": rows,
        "data": str(data_path),
        "selection_metric": "mean of temporal and neighborhood MAPE",
        "winner": winner.model_family,
        "results": [asdict(item) for item in results],
    }
    (output_dir / "benchmark-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    (output_dir / "benchmark-winner.json").write_text(
        json.dumps({"model_family": winner.model_family, "seed": seed, "rows": rows}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", type=int, default=2400)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output-dir", type=Path, default=Path("benchmarks"))
    args = parser.parse_args()
    print(json.dumps(run(args.rows, args.seed, args.output_dir), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
