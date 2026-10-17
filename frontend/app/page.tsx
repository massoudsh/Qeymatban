import Link from "next/link";
import { Sidebar } from "../components/dashboard/sidebar";
import { StatCard } from "../components/dashboard/stat-card";
import { Badge } from "../components/ui/badge";
import { Card } from "../components/ui/card";
import { fetchDashboardData, type ValuationHistoryItem } from "../lib/dashboard-api";

export const dynamic = "force-dynamic";

const money = (value: number | null) =>
  value === null
    ? "—"
    : new Intl.NumberFormat("fa-IR", { notation: "compact", maximumFractionDigits: 1 }).format(value) + " تومان";

const percent = (value: number | null) =>
  value === null ? "—" : new Intl.NumberFormat("fa-IR", { style: "percent", maximumFractionDigits: 0 }).format(value);

const date = (value: string) =>
  new Intl.DateTimeFormat("fa-IR", { day: "numeric", month: "long", year: "numeric" }).format(new Date(value));

function statusFor(item: ValuationHistoryItem) {
  if (item.confidence_level >= 0.8) return { tone: "success" as const, label: "اطمینان بالا" };
  if (item.confidence_level >= 0.7) return { tone: "neutral" as const, label: "تکمیل شده" };
  return { tone: "warning" as const, label: "اطمینان پایین" };
}

export default async function Dashboard() {
  const { history, stats } = await fetchDashboardData();
  const items = history?.slice(0, 4) ?? [];

  return (
    <div className="appShell">
      <Sidebar />
      <main className="mainContent">
        <header className="pageHeader">
          <div>
            <span className="sectionKicker">{new Intl.DateTimeFormat("fa-IR", { weekday: "long", day: "numeric", month: "long", year: "numeric" }).format(new Date())}</span>
            <h1>صبح بخیر، مدیر دفتر</h1>
            <p>تصمیم‌های امروز را با داده‌های روشن شروع کنید.</p>
          </div>
          <div className="headerActions">
            <Badge tone={stats ? "success" : "warning"}><i className="statusDot" /> {stats ? "موتور تحلیل فعال" : "سرویس در دسترس نیست"}</Badge>
            <button className="iconButton" aria-label="اعلان‌ها">♢</button>
          </div>
        </header>

        <section className="dashboardHero">
          <div>
            <span className="heroBadge">نسخهٔ جدید موتور ارزش‌گذاری</span>
            <h2>ارزش هر ملک را<br /><strong>با اطمینان توضیح دهید.</strong></h2>
            <p>از بازهٔ قیمت تا نزدیک‌ترین فایل‌های مشابه؛ همه‌چیز برای یک تصمیم مستند آماده است.</p>
            <Link className="uiButton uiButton-primary uiButton-lg" href="/valuation">شروع ارزش‌گذاری <span>←</span></Link>
          </div>
          <div className="heroOrb"><span>٪</span><small>توضیح‌پذیر<br />و داده‌محور</small></div>
        </section>

        <section className="statsGrid">
          <StatCard label="تحلیل‌های ثبت‌شده" value={stats ? new Intl.NumberFormat("fa-IR").format(stats.total_valuations) : "—"} detail={stats ? `${new Intl.NumberFormat("fa-IR").format(stats.last_30_days)} مورد در ۳۰ روز اخیر` : "اتصال به سرویس برقرار نشد"} icon="↗" />
          <StatCard label="میانگین اطمینان" value={percent(stats?.average_confidence ?? null)} detail="بر اساس تحلیل‌های ثبت‌شده" icon="◌" tone="amber" />
          <StatCard label="قیمت میانی غالب" value={money(stats?.median_price_mid ?? null)} detail="میانهٔ برآوردهای مدل" icon="◈" tone="coral" />
        </section>

        <section className="dashboardGrid" id="history">
          <Card className="activityCard">
            <div className="cardToolbar"><div><span className="sectionKicker">تاریخچه</span><h2>آخرین تحلیل‌ها</h2></div><Link href="/valuation">ارزش‌گذاری جدید ←</Link></div>
            <div className="activityTable">
              <div className="tableHead"><span>ملک</span><span>تاریخ</span><span>برآورد</span><span>وضعیت</span></div>
              {items.length ? items.map((item) => {
                const status = statusFor(item);
                return (
                  <div className="tableRow" key={item.valuation_id}>
                    <strong>{item.title}</strong>
                    <span>{date(item.created_at)}</span>
                    <b>{money(item.price_mid)}</b>
                    <Badge tone={status.tone}>{status.label}</Badge>
                  </div>
                );
              }) : <div className="tableEmpty">هنوز تحلیلی ثبت نشده است. اولین ارزش‌گذاری را شروع کنید.</div>}
            </div>
          </Card>
          <Card className="insightCard">
            <span className="sectionKicker">بینش</span>
            <h2>{stats && stats.total_valuations > 0 ? "تحلیل‌ها از موتور واقعی می‌آیند" : "منتظر اولین تحلیل"}</h2>
            <p>{stats && stats.total_valuations > 0 ? "همهٔ اعداد این داشبورد از نتیجهٔ ثبت‌شدهٔ ارزش‌گذاری‌ها خوانده می‌شوند." : "بعد از اولین ارزش‌گذاری، آمار و تاریخچه در همین داشبورد به‌روز می‌شوند."}</p>
            <div className="insightMeter"><span style={{ width: stats && stats.total_valuations > 0 ? "72%" : "0%" }} /></div>
            <div className="insightFooter"><strong>{stats ? percent(stats.average_confidence) : "—"}</strong><span>میانگین اطمینان مدل</span></div>
          </Card>
        </section>

        <section className="quickSection" id="how">
          <div><span className="sectionKicker">سه لایهٔ اعتماد</span><h2>از حدس بازار تا تصمیم مستند</h2></div>
          <div className="quickSteps">
            <article><b>۰۱</b><h3>بازه، نه عدد قطعی</h3><p>عدم‌قطعیت بازار را پنهان نمی‌کنیم.</p></article>
            <article><b>۰۲</b><h3>مقایسهٔ واقعی</h3><p>نزدیک‌ترین معاملات را مبنای تحلیل می‌کنیم.</p></article>
            <article><b>۰۳</b><h3>توضیح شفاف</h3><p>اثر هر ویژگی را قابل مشاهده می‌کنیم.</p></article>
          </div>
        </section>

        <footer className="appFooter"><strong>قیمت‌بان</strong><span>ابزار تصمیم‌یار است، نه جایگزین ارزیابی کارشناس.</span></footer>
      </main>
    </div>
  );
}
