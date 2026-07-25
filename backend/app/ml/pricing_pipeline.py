import joblib
import numpy as np
import pandas as pd
import xgboost as xgb

# ستون‌های ویژگی — باید با ستون‌های properties در schema.sql و PropertyFeatures همخوان باشد
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


class PricingModel:
    """مدل پایه پیش‌بینی قیمت (نقطه‌ای) روی داده تابولار با XGBoost."""

    def __init__(self) -> None:
        self.model = xgb.XGBRegressor(
            n_estimators=300,
            max_depth=6,
            learning_rate=0.05,
            objective="reg:squarederror",
        )

    def fit(self, df: pd.DataFrame, target_col: str = "sold_price") -> None:
        self.model.fit(df[FEATURE_COLUMNS], df[target_col])

    def predict(self, df: pd.DataFrame) -> np.ndarray:
        return self.model.predict(df[FEATURE_COLUMNS])

    def save(self, path: str) -> None:
        joblib.dump(self.model, path)

    def load(self, path: str) -> None:
        self.model = joblib.load(path)
