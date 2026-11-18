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

تصویر چندمرحله‌ای است. کانتینر با root شروع می‌شود تا مالکیت volumeها را اصلاح کند، سپس `docker/entrypoint.py` با `setuid` به `qeymatban` (uid 10001) می‌افتد. مسیرهای پیش‌فرض داخل کانتینر: `/app/models` (artifact)، `/app/data` (CSV و SQLite fallback) و `/app/benchmarks`.

تصویر runtime هیچ بستهٔ apt ندارد؛ wheel رسمی XGBoost خودش `libgomp` را همراه دارد. فقط target `benchmark` به `libgomp1` نیاز دارد (wheel LightGBM آن را همراه ندارد) و آن هم opt-in است. اگر PyPI کند است، میرور بدهید:

```bash
docker build --build-arg PIP_INDEX_URL=https://mirror.example/simple -t qeymatban-backend .
```

```bash
docker compose run --rm backend python -m app.scripts.train_model /app/data/transactions.csv --output-dir /app/models --promote
docker compose restart backend
docker build --target dev -t qeymatban-backend:dev . && docker run --rm qeymatban-backend:dev   # pytest
docker compose run --rm benchmark python -m app.scripts.benchmark_models --output-dir /app/benchmarks   # + CatBoost/LightGBM
```

`requirements.txt` فقط وابستگی‌های سرویس‌دهی است. `requirements-benchmark.txt` مدل‌های اضافی benchmark (CatBoost، LightGBM) را اضافه می‌کند و target `benchmark` آن را نصب می‌کند. TabPFN به‌دلیل PyTorch در هیچ‌کدام نیست؛ در صورت نیاز جداگانه نصب کنید.

Dockerfile با BuildKit cache mount برای pip و apt ساخته می‌شود؛ اگر شبکه هنگام دانلود wheel قطع شد، `PIP_RETRIES` و timeout بالاتر تنظیم شده‌اند و اجرای دوبارهٔ build از cache ادامه می‌دهد.

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

## Retrain دوره‌ای، نسخه‌بندی و rollback

`retrain` از جدول `transactions` آموزش می‌دهد، متریک‌ها را در جدول `model_versions` ثبت می‌کند و فقط وقتی نسخهٔ جدید از نسخهٔ جاری بدتر نباشد آن را promote می‌کند (تحمل پیش‌فرض ۲٪).

```bash
python -m app.scripts.retrain                       # آموزش از دیتابیس
python -m app.scripts.retrain --data data/x.csv     # یا از CSV
python -m app.scripts.retrain --rollback            # بازگرداندن نسخهٔ قبلی
python -m app.scripts.evaluate --model models/current.joblib --data golden.csv
```

برای زمان‌بندی، همان دستور را در cron بگذارید:

```cron
0 3 * * * cd /srv/qeymatban/backend && .venv/bin/python -m app.scripts.retrain --output-dir models >> /var/log/qeymatban-retrain.log 2>&1
```

`evaluate` روی یک dataset طلایی، MAPE و نسبت MAE را می‌سنجد و در صورت عبور از آستانه با کد خروجی غیرصفر تمام می‌شود؛ مناسب برای gate کردن استقرار.

## ورود داده به دیتابیس

```bash
python -m app.scripts.import_transactions raw.csv data/transactions.csv --to-database
# یا فقط بارگذاری فایل از قبل اعتبارسنجی‌شده:
python -m app.scripts.load_database data/transactions.csv
```

بارگذاری idempotent است (شناسهٔ تراکنش کلید یکتاست) و برای هر ملک `feature_embedding` می‌سازد.

## API

- `GET /health` — سلامت process
- `GET /v1/model/status` — آمادگی و نسخه مدل
- `GET /v1/model/versions` — نسخه‌های ثبت‌شده، متریک‌ها، نسخهٔ جاری و اختلاف MAPE
- `POST /v1/valuations` — بازه قیمت، confidence، SHAP، comparables و `valuation_id` ذخیره‌شده
- `GET /v1/valuations?limit=20` — تاریخچهٔ ارزش‌گذاری‌ها برای داشبورد
- `GET /v1/valuations/stats` — تعداد، میانگین confidence، تحلیل‌های ۳۰ روز اخیر و میانهٔ قیمت

اگر `QEYMATBAN_API_KEYS` تنظیم شود، همهٔ endpointهای `/v1/valuations` و `/v1/model/versions` هدر `X-API-Key` معتبر می‌خواهند. چند کلید با کاما جدا می‌شوند.

## لاگ‌ها

لاگ‌ها به‌صورت JSON و یک‌شیء در هر خط با `request_id`، مسیر، status و `duration_ms` نوشته می‌شوند. برای خروجی خوانا در توسعه:

```bash
LOG_FORMAT=plain LOG_LEVEL=DEBUG uvicorn app.main:app --reload
```

هر پاسخ هدر `X-Request-Id` برمی‌گرداند تا بتوان لاگ را به درخواست کاربر وصل کرد.

## دیتابیس

Schema اولیه در `migrations/001_init.sql` نیازمند PostgreSQL 15+، PostGIS و pgvector است. ارجاع Docker به‌صورت پیش‌فرض `postgres:16` ساده است؛ برای PostGIS/pgvector از `compose.geo.yaml` استفاده کنید. در اجرای محلی، `DATABASE_URL` به‌صورت پیش‌فرض SQLite است و API هنگام startup جدول‌ها را می‌سازد. جداول اصلی: `properties`، `transactions`، `valuations` و `valuation_comparables`. هر درخواست موفق `POST /v1/valuations` ملک، نتیجه مدل و comparables معتبر را ذخیره می‌کند.

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
