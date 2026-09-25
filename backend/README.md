# Qeymatban Backend

API و pipeline نسخه‌پذیر ارزش‌گذاری (FastAPI + Python).

## اجرا (روی سرور)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

## آماده‌سازی داده و مدل

ورودی شریک داده باید CSV و شامل `sold_price` و همه ستون‌های ویژگی باشد. ابتدا داده را اعتبارسنجی و یکدست کنید، سپس مدل نسخه‌دار بسازید:

```bash
python -m app.scripts.import_transactions raw.csv data/transactions.csv
python -m app.scripts.train_model data/transactions.csv --output-dir models
ln -sfn valuation-<version>.joblib models/current.joblib
```

هر artifact شامل مدل قیمت، مدل‌های quantile، جست‌وجوی فایل مشابه و نسخه مدل است. فایل JSON کنار آن MAE و MAPE داده validation را نگه می‌دارد. حداقل ۲۰ معامله معتبر لازم است؛ داده واقعی داخل repository ذخیره نمی‌شود.

## API

- `GET /health` — سلامت process
- `GET /v1/model/status` — آمادگی و نسخه مدل
- `POST /v1/valuations` — بازه قیمت، confidence، SHAP، comparables و `valuation_id` ذخیره‌شده

اگر `QEYMATBAN_API_KEYS` تنظیم شود، endpoint ارزش‌گذاری هدر `X-API-Key` معتبر می‌خواهد. چند کلید با کاما جدا می‌شوند.

## دیتابیس

Schema اولیه در `migrations/001_init.sql` نیازمند PostgreSQL 15+، PostGIS و pgvector است. در اجرای محلی، `DATABASE_URL` به‌صورت پیش‌فرض SQLite است و API هنگام startup جدول‌ها را می‌سازد. جداول اصلی: `properties`، `transactions`، `valuations` و `valuation_comparables`. هر درخواست موفق `POST /v1/valuations` ملک، نتیجه مدل و comparables معتبر را ذخیره می‌کند.

## تست

```bash
pip install -r requirements-dev.txt
pytest -q
ruff check app tests
```
