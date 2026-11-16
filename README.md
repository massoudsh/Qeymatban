# Qeymatban (قیمت‌بان)

**لایه اعتماد بازار املاک ایران — تبدیل قیمت مبهم به توضیح قابل دفاع.**

## مسئله

در بازار املاک ایران، قیمت‌گذاری هنوز بیش از حد به حافظه، تجربه و مقایسه‌های شفاهی مشاور وابسته است، نه به تحلیل قابل مشاهده و قابل دفاع. همین ابهام باعث بی‌اعتمادی خریدار، مذاکره فرسایشی و کندی معامله می‌شود.

## راه‌حل

Qeymatban با استفاده از هوش مصنوعی، قیمت یک ملک را از یک عدد خام به یک **توضیح ساختاریافته** تبدیل می‌کند:

- بازه قیمت پیشنهادی و میزان عدم قطعیت
- فایل‌های مشابه (comparables) که مبنای مقایسه بوده‌اند
- سهم هر ویژگی (متراژ، سن بنا، طبقه، نور، ویو، پارکینگ، بازسازی، دسترسی و...) در قیمت نهایی

هدف جایگزینی مشاور نیست؛ شفاف کردن منطق ارزش‌گذاری برای مشاور، مالک و خریدار است.

## مخاطبان اولیه

- دفاتر املاک حرفه‌ای
- پلتفرم‌های آگهی ملک
- سرمایه‌گذاران ملکی و شرکت‌های مدیریت دارایی
- نهادهای مالی (وام، وثیقه، تصمیم سرمایه‌گذاری)

## مدل درآمدی

- SaaS برای دفاتر و پلتفرم‌های آگهی (B2B)
- API ارزش‌گذاری برای مؤسسات مالی و بازیگران بزرگ‌تر بازار

## ساختار پروژه

```
backend/    FastAPI + مدل ارزش‌گذاری (Python)
frontend/   پنل Next.js
docs/       چشم‌انداز و معماری فنی
compose.yaml  استک کامل Docker: دیتابیس + API + پنل
```

## اجرا با Docker

کل استک (PostgreSQL با PostGIS و pgvector، API و پنل) با Compose بالا می‌آید:

```bash
cp .env.example .env      # رمز دیتابیس و کلیدهای API را تنظیم کنید
docker compose up --build
```

- پنل: `http://localhost:3000`
- API: `http://localhost:8000` (مستندات تعاملی: `/docs`)
- سلامت API: `GET /health` — پنل: `/api/health`

جزئیات مهم:

- پورت‌ها با `FRONTEND_PORT` و `BACKEND_PORT` قابل تغییرند؛ پورت دیتابیس به بیرون منتشر نمی‌شود.
- اگر `QEYMATBAN_API_KEYS` را تنظیم کردید، همان مقدار را در `QEYMATBAN_API_KEY` هم بگذارید تا پنل به API دسترسی داشته باشد.
- داده‌های دیتابیس، artifact مدل، خروجی benchmark و فایل‌های دادهٔ برنامه در volumeهای `pgdata`، `models`، `benchmarks` و `appdata` نگه‌داری می‌شوند.
- API بدون artifact مدل بالا می‌آید ولی `POST /v1/valuations` پاسخ 503 می‌دهد تا مدل آموزش داده شود.
- جدول‌ها هنگام startup از ORM ساخته می‌شوند. `backend/migrations/001_init.sql` نسخهٔ کامل جغرافیایی است و فقط وقتی ستون‌های `location` و `feature_embedding` واقعاً پر می‌شوند باید اجرا شود؛ اجرای آن پیش از ORM به‌دلیل `location NOT NULL` با نوشتن‌های فعلی API سازگار نیست.
- تصویر API شامل TabPFN و PyTorch است و حجم بالایی دارد؛ اگر فقط مدل‌های درختی لازم است، `tabpfn` را از `backend/requirements.txt` حذف کنید.

### آموزش مدل داخل کانتینر

```bash
docker compose run --rm backend python -m app.scripts.benchmark_models --rows 2400 --seed 42 --output-dir /app/benchmarks
docker compose run --rm backend python -m app.scripts.train_model /app/benchmarks/mock-transactions.csv \
  --benchmark-winner /app/benchmarks/benchmark-winner.json --output-dir /app/models --version dev-local --promote
docker compose restart backend
```

برای دادهٔ واقعی، CSV تأییدشده را به کانتینر mount کنید و مسیر آن را به `import_transactions` بدهید:

```bash
docker compose run --rm -v "$PWD/data:/data:ro" backend \
  python -m app.scripts.import_transactions /data/raw.csv /app/data/transactions.csv
```

### تست در تصویر Docker

```bash
docker build --target dev -t qeymatban-backend:dev ./backend
docker run --rm qeymatban-backend:dev
```

## مستندات بیشتر

- چشم‌انداز کامل محصول: [`docs/vision.md`](docs/vision.md)
- معماری فنی و stack: [`docs/architecture.md`](docs/architecture.md)

## وضعیت

MVP فنی آماده است: API ارزش‌گذاری artifact نسخه‌دار را بارگذاری می‌کند، مسیر import و آموزش داده وجود دارد، پنل مدرن RTL به API متصل است و CI تست‌های بک‌اند و type-check فرانت‌اند را اجرا می‌کند. برای تولید خروجی واقعی باید داده معاملات معتبر تأمین و مدل روی سرور آموزش داده شود.
