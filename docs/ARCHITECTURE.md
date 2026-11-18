# Architecture

One page: how a valuation request flows through the system, and what each
component is responsible for.

## Data flow

```
                    ┌──────────────────────────────────────────────┐
  Broker / API      │  Next.js dashboard (RTL, standalone build)   │
  client  ─────────►│  app/api/valuations  (server-side BFF)       │
                    └───────────────────┬──────────────────────────┘
                                        │ QEYMATBAN_API_URL + X-API-Key
                                        ▼
                    ┌──────────────────────────────────────────────┐
                    │  FastAPI  (backend/app/main.py)              │
                    │  ├─ require_api_key    optional auth         │
                    │  ├─ RequestContextMiddleware  request id/log │
                    │  └─ POST /v1/valuations                      │
                    └───────────────────┬──────────────────────────┘
                                        ▼
                    ┌──────────────────────────────────────────────┐
                    │  ValuationService  (app/ml/)                 │
                    │  ├─ PricingModel      XGBoost point estimate │
                    │  ├─ UncertaintyEstimator  quantile band      │
                    │  ├─ ComparablesFinder  cosine neighbours     │
                    │  └─ explain_prediction  SHAP contributions   │
                    └───────────────────┬──────────────────────────┘
                                        ▼
                    ┌──────────────────────────────────────────────┐
                    │  PostgreSQL  (properties, transactions,      │
                    │  valuations, valuation_comparables,          │
                    │  model_versions)                             │
                    └──────────────────────────────────────────────┘
```

## Components

| Component | Path | Responsibility |
|---|---|---|
| API | `backend/app/main.py` | HTTP surface, auth, persistence of each valuation |
| Logging | `backend/app/logging_config.py` | JSON logs, per-request id, duration |
| Valuation engine | `backend/app/ml/valuation_service.py` | Orchestrates price, interval, comparables, explanations |
| Dataset access | `backend/app/ml/dataset.py` | Joins transactions to properties, feature embeddings |
| Retraining | `backend/app/scripts/retrain.py` | Trains, compares to current, promotes or rejects, rollback |
| Evaluation | `backend/app/scripts/evaluate.py` | Golden-dataset regression gate with thresholds |
| Import | `backend/app/scripts/import_transactions.py`, `load_database.py` | Validate CSV, then load into the database |
| Dashboard | `frontend/app/` | RTL panel, history and KPIs, printable report |

## Model lifecycle

1. `import_transactions` validates a partner export and writes a canonical CSV.
2. `load_database` inserts properties and transactions, computing feature embeddings.
3. `retrain` trains a versioned artifact, records metrics in `model_versions`, and
   promotes it only when MAPE is not worse than the current version (2% tolerance).
4. `evaluate` scores the promoted artifact against a golden dataset and exits
   non-zero when a threshold is missed.
5. `retrain --rollback` re-promotes the previous version; the API loads
   `models/current.joblib` at startup.

## Trust boundaries

- The browser never sees the API key; only the Next.js server-side routes hold it.
- Data files and model artifacts are never committed (see `.gitignore`).
- The model artifact is loaded from disk at startup, so artifact integrity is a
  deployment concern rather than a runtime one.
