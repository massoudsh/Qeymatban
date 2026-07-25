# Qeymatban Backend

API و مدل ارزش‌گذاری (FastAPI + Python).

## اجرا (روی سرور، نه داخل کانتینر توسعه)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## دیتابیس

Schema اولیه در [`migrations/001_init.sql`](migrations/001_init.sql) — نیازمند PostgreSQL 15+ با پسوند‌های `postgis` و `pgvector`.

جداول اصلی:
- `properties` — هر فایل/ملک (فعال یا فروخته‌شده) با موقعیت جغرافیایی و ویژگی‌ها
- `transactions` — معاملات واقعاً بسته‌شده (داده آموزشی مدل)
- `valuations` — خروجی مدل: بازه قیمت، عدم قطعیت، SHAP values (audit trail قابل دفاع)
- `valuation_comparables` — فایل‌های مشابه استفاده‌شده در هر ارزش‌گذاری

## Pipeline مدل ارزش‌گذاری (`app/ml/`)

| ماژول | نقش |
|---|---|
| `pricing_pipeline.py` | مدل پایه قیمت (XGBoost regression) |
| `uncertainty.py` | بازه قیمت با quantile regression (XGBoost) |
| `comparables.py` | فایل‌های مشابه با شباهت برداری (StandardScaler + NearestNeighbors) |
| `explain.py` | سهم هر ویژگی در قیمت (SHAP) |
| `valuation_service.py` | orchestrator: `fit(historical_df)` سپس `valuate(target_df)` |

نکته: این pipeline هنوز به هیچ endpoint وصل نشده چون داده آموزشی واقعی (از جدول `transactions`) موجود نیست. وقتی داده جمع‌آوری شد، `ValuationService` باید در startup اپ لود/train شود و از طریق یک endpoint (مثلاً `POST /valuations`) در دسترس قرار گیرد.
