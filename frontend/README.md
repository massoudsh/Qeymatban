# Qeymatban Frontend

پنل RTL قیمت‌بان با تم فیروزه‌ای برای ورود مشخصات ملک و نمایش بازه قیمت، عوامل اثرگذار و فایل‌های مشابه.

## قابلیت‌های رقابتی

- زمینهٔ محله، قیمت هر متر و تعداد نمونهٔ مرجع در نتیجه
- confidence، نسخهٔ مدل و provenance داده
- سناریوهای وضعیت فعلی، بازسازی‌شده و فروش سریع
- گزارش چاپی برای ارائه یا بایگانی
- داشبورد تاریخچه و KPI متصل به API واقعی

## پاک‌سازی

تنها `next.config.ts` تنظیمات Next.js را نگه می‌دارد؛ فایل تکراری `next.config.mjs` حذف شده است.

## ساختار UI

- `/` — داشبورد مدیریتی با کارت‌های KPI، تاریخچه تحلیل و CTA ارزش‌گذاری
- `/valuation` — فرم کامل ارزش‌گذاری و پنل نتیجه
- `components/ui/` — کامپوننت‌های محلی Button، Card، Badge و Progress بر اساس الگوی فیروزه‌ای
- `components/dashboard/` — Sidebar، کارت‌های آماری و workspace ارزش‌گذاری

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
