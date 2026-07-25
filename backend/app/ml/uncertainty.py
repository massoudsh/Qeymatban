import numpy as np
import pandas as pd
import xgboost as xgb

from .pricing_pipeline import FEATURE_COLUMNS


class UncertaintyEstimator:
    """تخمین بازه قیمت (به‌جای عدد قطعی) با quantile regression روی XGBoost.

    دو مدل جداگانه برای صدک پایین و بالا آموزش داده می‌شود تا بازه اطمینان
    (پیش‌فرض ۱۰٪ تا ۹۰٪ ≈ بازه ۸۰٪) تولید شود.
    """

    def __init__(self, lower_q: float = 0.1, upper_q: float = 0.9) -> None:
        self.lower_q = lower_q
        self.upper_q = upper_q
        self.lower_model = xgb.XGBRegressor(
            objective="reg:quantileerror",
            quantile_alpha=lower_q,
            n_estimators=300,
            max_depth=6,
            learning_rate=0.05,
        )
        self.upper_model = xgb.XGBRegressor(
            objective="reg:quantileerror",
            quantile_alpha=upper_q,
            n_estimators=300,
            max_depth=6,
            learning_rate=0.05,
        )

    def fit(self, df: pd.DataFrame, target_col: str = "sold_price") -> None:
        X = df[FEATURE_COLUMNS]
        y = df[target_col]
        self.lower_model.fit(X, y)
        self.upper_model.fit(X, y)

    def predict_interval(self, df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
        X = df[FEATURE_COLUMNS]
        return self.lower_model.predict(X), self.upper_model.predict(X)
