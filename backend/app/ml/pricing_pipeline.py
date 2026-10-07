import joblib
import numpy as np
import pandas as pd
import xgboost as xgb

FEATURE_COLUMNS = [
    "area_sqm",
    "year_built",
    "floor",
    "total_floors",
    "rooms",
    "has_parking",
    "has_elevator",
    "has_storage",
    "renovated",
    "light_score",
    "view_score",
    "access_score",
]

MODEL_FAMILIES = ("xgboost", "catboost", "lightgbm", "tabpfn")


def create_regressor(model_family: str):
    if model_family == "xgboost":
        return xgb.XGBRegressor(
            n_estimators=400,
            max_depth=6,
            learning_rate=0.04,
            subsample=0.85,
            colsample_bytree=0.9,
            objective="reg:squarederror",
            random_state=42,
            n_jobs=1,
        )
    if model_family == "catboost":
        from catboost import CatBoostRegressor

        return CatBoostRegressor(
            iterations=400,
            depth=7,
            learning_rate=0.04,
            loss_function="MAE",
            random_seed=42,
            verbose=False,
            thread_count=1,
        )
    if model_family == "lightgbm":
        from lightgbm import LGBMRegressor

        return LGBMRegressor(
            n_estimators=400,
            learning_rate=0.04,
            num_leaves=31,
            subsample=0.85,
            colsample_bytree=0.9,
            random_state=42,
            n_jobs=1,
            verbosity=-1,
        )
    if model_family == "tabpfn":
        from tabpfn import TabPFNRegressor

        return TabPFNRegressor(random_state=42)
    raise ValueError(f"Unsupported model family: {model_family}")


class PricingModel:
    """A selected tabular regressor used by the valuation engine."""

    def __init__(self, model_family: str = "xgboost") -> None:
        if model_family not in MODEL_FAMILIES:
            raise ValueError(f"model_family must be one of: {', '.join(MODEL_FAMILIES)}")
        self.model_family = model_family
        self.model = create_regressor(model_family)
        self.feature_baseline: pd.Series | None = None

    def fit(self, df: pd.DataFrame, target_col: str = "sold_price") -> None:
        features = df[FEATURE_COLUMNS]
        self.feature_baseline = features.median(numeric_only=True).reindex(FEATURE_COLUMNS).fillna(0)
        self.model.fit(features, df[target_col])

    def predict(self, df: pd.DataFrame) -> np.ndarray:
        return np.asarray(self.model.predict(df[FEATURE_COLUMNS]))

    def save(self, path: str) -> None:
        joblib.dump(self, path)

    def load(self, path: str) -> None:
        loaded = joblib.load(path)
        if not isinstance(loaded, PricingModel):
            raise TypeError("Model artifact is not a PricingModel")
        self.model_family = loaded.model_family
        self.model = loaded.model
        self.feature_baseline = loaded.feature_baseline
