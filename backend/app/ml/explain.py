import pandas as pd
import shap

from .pricing_pipeline import FEATURE_COLUMNS


def explain_prediction(model, row: pd.DataFrame) -> dict[str, float]:
    """سهم هر ویژگی در قیمت پیش‌بینی‌شده (SHAP values) — هسته توضیح‌پذیری قیمت."""
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(row[FEATURE_COLUMNS])
    return dict(zip(FEATURE_COLUMNS, shap_values[0].tolist()))
