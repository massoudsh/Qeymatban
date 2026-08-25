from pathlib import Path

import joblib
import pandas as pd

from .comparables import ComparablesFinder
from .explain import explain_prediction
from .pricing_pipeline import PricingModel
from .uncertainty import UncertaintyEstimator


class ValuationService:
    """نقطه ورود واحد pipeline ارزش‌گذاری: قیمت + بازه عدم قطعیت + comparables + توضیح SHAP.

    استفاده:
        service = ValuationService()
        service.fit(historical_df)          # historical_df از جدول transactions/properties
        result = service.valuate(target_df) # target_df یک ردیف با ستون‌های FEATURE_COLUMNS
    """

    def __init__(self, model_version: str = "unversioned") -> None:
        self.model_version = model_version
        self.pricing_model = PricingModel()
        self.uncertainty = UncertaintyEstimator()
        self.comparables = ComparablesFinder()

    def fit(self, historical_df: pd.DataFrame, target_col: str = "sold_price") -> None:
        self.pricing_model.fit(historical_df, target_col)
        self.uncertainty.fit(historical_df, target_col)
        self.comparables.fit(historical_df)

    def valuate(self, target_property: pd.DataFrame) -> dict:
        price_mid = float(self.pricing_model.predict(target_property)[0])
        low_predictions, high_predictions = self.uncertainty.predict_interval(target_property)
        price_low = min(float(low_predictions[0]), price_mid)
        price_high = max(float(high_predictions[0]), price_mid)
        shap_contrib = explain_prediction(self.pricing_model.model, target_property)
        comps = self.comparables.find(target_property)[0]

        return {
            "price_low": price_low,
            "price_mid": price_mid,
            "price_high": price_high,
            "confidence_level": self.uncertainty.upper_q - self.uncertainty.lower_q,
            "model_version": self.model_version,
            "feature_contributions": shap_contrib,
            "comparables": comps,
        }

    def save(self, path: str | Path) -> None:
        """Persist the fitted pipeline as one atomic model artifact."""
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, destination)

    @classmethod
    def load(cls, path: str | Path) -> "ValuationService":
        service = joblib.load(path)
        if not isinstance(service, cls):
            raise TypeError("Model artifact is not a ValuationService")
        return service
