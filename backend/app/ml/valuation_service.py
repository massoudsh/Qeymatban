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

    def __init__(self) -> None:
        self.pricing_model = PricingModel()
        self.uncertainty = UncertaintyEstimator()
        self.comparables = ComparablesFinder()

    def fit(self, historical_df: pd.DataFrame, target_col: str = "sold_price") -> None:
        self.pricing_model.fit(historical_df, target_col)
        self.uncertainty.fit(historical_df, target_col)
        self.comparables.fit(historical_df)

    def valuate(self, target_property: pd.DataFrame) -> dict:
        price_mid = float(self.pricing_model.predict(target_property)[0])
        price_low, price_high = self.uncertainty.predict_interval(target_property)
        shap_contrib = explain_prediction(self.pricing_model.model, target_property)
        comps = self.comparables.find(target_property)[0]

        return {
            "price_low": float(price_low[0]),
            "price_mid": price_mid,
            "price_high": float(price_high[0]),
            "feature_contributions": shap_contrib,
            "comparables": comps,
        }
