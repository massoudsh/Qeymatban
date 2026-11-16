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

## اجرا با Docker

از ریشهٔ پروژه:

```bash
docker compose up --build backend   # همراه با سرویس db
```

تصویر چندمرحله‌ای است، با کاربر غیرروت (`qeymatban`) اجرا می‌شود و entrypoint پیش از بالا آمدن API، مالکیت volumeها را اصلاح و تا آماده‌شدن PostgreSQL صبر می‌کند. مسیرهای پیش‌فرض داخل کانتینر: `/app/models` (artifact)، `/app/data` (CSV و SQLite fallback) و `/app/benchmarks`.

```bash
docker compose run --rm backend python -m app.scripts.train_model /app/data/transactions.csv --output-dir /app/models --promote
docker compose restart backend
docker build --target dev -t qeymatban-backend:dev . && docker run --rm qeymatban-backend:dev   # pytest
```

تصویر runtime کل requirements از جمله TabPFN/PyTorch را نصب می‌کند؛ برای کاهش حجم، `tabpfn` را حذف کنید.

## آماده‌سازی داده و مدل

ورودی شریک داده باید CSV و شامل `sold_price` و همه ستون‌های ویژگی باشد. ابتدا داده را اعتبارسنجی و یکدست کنید، سپس مدل نسخه‌دار بسازید:

```bash
python -m app.scripts.import_transactions raw.csv data/transactions.csv
python -m app.scripts.train_model data/transactions.csv --output-dir models
ln -sfn valuation-<version>.joblib models/current.joblib
```

هر artifact شامل مدل قیمت، مدل‌های quantile، جست‌وجوی فایل مشابه و نسخه مدل است. فایل JSON کنار آن MAE و MAPE داده validation را نگه می‌دارد. حداقل ۲۰ معامله معتبر لازم است؛ داده واقعی داخل repository ذخیره نمی‌شود.

## Benchmark تکرارپذیر مدل‌ها

برای مقایسهٔ منصفانهٔ XGBoost، CatBoost، LightGBM و TabPFN، ابتدا dataset مصنوعی seedدار تولید و هر مدل با split زمانی و holdout محله ارزیابی می‌شود. معیار انتخاب، میانگین MAPE دو split است؛ ensemble ساخته نمی‌شود و فقط مدل برنده وارد artifact می‌شود.

```bash
python -m app.scripts.benchmark_models --rows 2400 --seed 42 --output-dir benchmarks
python -m app.scripts.train_model benchmarks/mock-transactions.csv \
  --benchmark-winner benchmarks/benchmark-winner.json --output-dir models
ln -sfn valuation-<version>.joblib models/current.joblib
```

`mock-transactions.csv` فقط برای اعتبارسنجی فنی است و نباید معیار کیفیت یا مدل production تلقی شود. برای دادهٔ واقعی، همان benchmark را روی معاملات بسته‌شدهٔ canonical اجرا کنید و سپس winner file آن را به `train_model` بدهید.

## API

- `GET /health` — سلامت process
- `GET /v1/model/status` — آمادگی و نسخه مدل
- `POST /v1/valuations` — بازه قیمت، confidence، SHAP، comparables و `valuation_id` ذخیره‌شده
- `GET /v1/valuations?limit=20` — تاریخچهٔ ارزش‌گذاری‌ها برای داشبورد
- `GET /v1/valuations/stats` — تعداد، میانگین confidence، تحلیل‌های ۳۰ روز اخیر و میانهٔ قیمت

اگر `QEYMATBAN_API_KEYS` تنظیم شود، همهٔ endpointهای `/v1/valuations` هدر `X-API-Key` معتبر می‌خواهند. چند کلید با کاما جدا می‌شوند.

## دیتابیس

Schema اولیه در `migrations/001_init.sql` نیازمند PostgreSQL 15+، PostGIS و pgvector است. در اجرای محلی، `DATABASE_URL` به‌صورت پیش‌فرض SQLite است و API هنگام startup جدول‌ها را می‌سازد. جداول اصلی: `properties`، `transactions`، `valuations` و `valuation_comparables`. هر درخواست موفق `POST /v1/valuations` ملک، نتیجه مدل و comparables معتبر را ذخیره می‌کند.

### PostgreSQL

```bash
export DATABASE_URL=postgresql+psycopg2://user:pass@host:5432/qeymatban
psql "$DATABASE_URL" -f migrations/001_init.sql   # فقط برای دیتابیس خالی
psql "$DATABASE_URL" -f migrations/002_orm_alignment.sql  # دیتابیس موجود
```

مدل‌های ORM روی PostgreSQL از نوع `uuid` استفاده می‌کنند و با SQLite (`CHAR(36)`) سازگارند. هنگام startup، ستون‌های ORM که در schema قدیمی نیستند (`listed_price`, `status`, `created_at`, `updated_at`, `confidence_level`) بدون حذف داده اضافه می‌شوند. `upgrade_postgres_schema()` هیچ مایگریشن مخربی اجرا نمی‌کند.

## تست

```bash
pip install -r requirements-dev.txt
pytest -q
ruff check app tests
```
