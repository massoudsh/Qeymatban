# Qeymatban Frontend

پنل RTL قیمت‌بان برای ورود مشخصات ملک و نمایش بازه قیمت، عوامل اثرگذار و فایل‌های مشابه.

## اجرا

بیلد و نصب dependencyهای Next.js را روی سرور انجام دهید:

```bash
cp .env.example .env.local
npm install
npm run dev
```

متغیر `QEYMATBAN_API_URL` آدرس داخلی FastAPI است. اگر API key فعال است، آن را در `QEYMATBAN_API_KEY` قرار دهید؛ این مقدار فقط در route سمت سرور خوانده می‌شود و به مرورگر ارسال نمی‌شود.

## اعتبارسنجی

```bash
npm run typecheck
npm run build
```
