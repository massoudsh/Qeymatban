import numpy as np
import pandas as pd
import shap

from .pricing_pipeline import FEATURE_COLUMNS


def explain_prediction(model, row: pd.DataFrame, feature_baseline: pd.Series | None = None) -> dict[str, float]:
    """Return SHAP values for tree models or deterministic marginal effects otherwise."""
    features = row[FEATURE_COLUMNS]
    try:
        shap_values = shap.TreeExplainer(model).shap_values(features)
        return dict(zip(FEATURE_COLUMNS, np.asarray(shap_values)[0].tolist()))
    except Exception:
        if feature_baseline is None:
            raise
        prediction = float(model.predict(features)[0])
        contributions: dict[str, float] = {}
        for column in FEATURE_COLUMNS:
            counterfactual = features.copy()
            counterfactual.loc[:, column] = feature_baseline[column]
            contributions[column] = prediction - float(model.predict(counterfactual)[0])
        return contributions
