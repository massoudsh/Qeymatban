"use client";

import { useEffect, useState } from "react";
import {
  Bell,
  Building2,
  ChevronDown,
  ChevronLeft,
  CircleHelp,
  FileText,
  Home,
  LayoutDashboard,
  MapPin,
  MoreHorizontal,
  Plus,
  Search,
  Settings2,
  Sparkles,
  TrendingUp,
  Users,
} from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Comparable = { id: string; title: string; area_sqm: number; year_built: number; floor: number; price: number; similarity: number };
type DashboardData = {
  stats: { valuations_this_month: number; model_accuracy: number; active_properties: number; pending_transactions: number };
  latest_valuation: { price_low: number; price_mid: number; price_high: number; confidence: number } | null;
  comparables: Comparable[];
};

const formatNumber = (value: number) => value.toLocaleString("fa-IR", { maximumFractionDigits: 1 });
const formatPrice = (value: number) => `${(value / 1_000_000_000).toLocaleString("fa-IR", { maximumFractionDigits: 1 })} میلیارد`;

const navItems = [
  { label: "نمای کلی", icon: LayoutDashboard, active: true },
  { label: "ارزش‌گذاری‌ها", icon: Sparkles },
  { label: "فایل‌های من", icon: Building2 },
  { label: "مشتری‌ها", icon: Users },
  { label: "گزارش‌ها", icon: FileText },
];

export default function HomePage() {
  const [activeNav, setActiveNav] = useState("نمای کلی");
  const [area, setArea] = useState("۱۴۸");
  const [neighborhood, setNeighborhood] = useState("نیاوران");
  const [notice, setNotice] = useState("");
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    fetch(`${API_BASE}/dashboard`)
      .then((response) => response.ok ? response.json() : Promise.reject(new Error("dashboard request failed")))
      .then(setDashboard)
      .catch(() => setNotice("اتصال به سرویس قیمت‌بان برقرار نشد"));
  }, []);

  async function runEstimate() {
    setIsSubmitting(true);
    try {
      const response = await fetch(`${API_BASE}/valuations`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ neighborhood, city: "تهران", title: `ملک ${neighborhood}`, area_sqm: Number(area.replace(/[٬،]/g, "")), year_built: 1400, floor: 3, total_floors: 5, rooms: 3, has_parking: true, has_elevator: true, has_storage: true, renovated: true, light_score: 5, view_score: 4, access_score: 5 }),
      });
      if (!response.ok) throw new Error("valuation request failed");
      const refreshed = await fetch(`${API_BASE}/dashboard`);
      setDashboard(await refreshed.json());
      setNotice(`ارزش‌گذاری جدید برای ملک ${area} متری آماده شد`);
    } catch {
      setNotice("ثبت ارزش‌گذاری انجام نشد؛ اتصال API را بررسی کنید");
    } finally {
      setIsSubmitting(false);
      window.setTimeout(() => setNotice(""), 3500);
    }
  }

  return (
    <main className="shell">
      <aside className="sidebar">
        <div className="brand"><span className="brand-mark"><Sparkles size={17} /></span><span>قیمت‌بان</span></div>
        <div className="workspace-switcher"><span className="avatar">م</span><span><b>مشاوران نیاوران</b><small>فضای کاری فعال</small></span><ChevronDown size={15} /></div>
        <nav className="nav-list" aria-label="ناوبری اصلی">
          <p className="nav-label">فضای کاری</p>
          {navItems.map(({ label, icon: Icon, active }) => <button key={label} className={`nav-item ${activeNav === label || (active && !activeNav) ? "active" : ""}`} onClick={() => setActiveNav(label)}><Icon size={18} /><span>{label}</span>{label === "ارزش‌گذاری‌ها" && <em>۱۲</em>}</button>)}
          <p className="nav-label nav-label-lower">مدیریت</p>
          <button className="nav-item"><Settings2 size={18} /><span>تنظیمات</span></button>
          <button className="nav-item"><CircleHelp size={18} /><span>راهنما و پشتیبانی</span></button>
        </nav>
        <div className="sidebar-foot"><div className="profile"><span className="avatar avatar-light">م</span><span><b>مریم احمدی</b><small>مشاور ارشد</small></span><MoreHorizontal size={17} /></div><div className="plan"><span>اشتراک حرفه‌ای</span><b>۲۳ روز باقی‌مانده</b><div className="progress"><i /></div></div></div>
      </aside>

      <section className="content">
        <header className="topbar"><div className="breadcrumb"><span>فضای کاری</span><ChevronLeft size={15} /><b>{activeNav}</b></div><div className="top-actions"><button className="icon-button" aria-label="جستجو"><Search size={19} /></button><button className="icon-button notification" aria-label="اعلان‌ها"><Bell size={19} /><i /></button><span className="top-divider" /><span className="date">سه‌شنبه، ۲۴ مهر ۱۴۰۳</span></div></header>
        <div className="page-heading"><div><p className="eyebrow">سه‌شنبه، روز خوبی برای تصمیم‌های دقیق است</p><h1>نمای کلی <span>فضای شما</span></h1><p className="subtitle">منطق قیمت‌گذاری فایل‌هایتان را شفاف‌تر ببینید.</p></div><button className="primary-button" onClick={() => document.getElementById("valuation-form")?.scrollIntoView({ behavior: "smooth" })}><Plus size={18} /> ارزش‌گذاری جدید</button></div>

        {notice && <div className="toast"><Sparkles size={17} />{notice}</div>}
        <div className="stat-grid"><StatCard label="ارزش‌گذاری‌های این ماه" value={dashboard ? formatNumber(dashboard.stats.valuations_this_month) : "—"} suffix="مورد" change="۱۸٪" icon={Sparkles} /><StatCard label="میانگین دقت مدل" value={dashboard ? formatNumber(dashboard.stats.model_accuracy) : "—"} suffix="٪" change="۲٫۱٪" icon={TrendingUp} /><StatCard label="فایل‌های فعال" value={dashboard ? formatNumber(dashboard.stats.active_properties) : "—"} suffix="فایل" change="۸٪" icon={Building2} /><StatCard label="معاملات در جریان" value={dashboard ? formatNumber(dashboard.stats.pending_transactions) : "—"} suffix="مورد" change="۵٪" icon={FileText} /></div>

        <div className="main-grid">
          <section className="panel valuation-panel" id="valuation-form"><div className="panel-heading"><div><span className="section-kicker">شروع سریع</span><h2>ارزش‌گذاری یک ملک</h2></div><span className="step-pill">۱ از ۳</span></div><p className="panel-intro">چند مشخصه اصلی را وارد کنید تا قیمت منصفانه و فایل‌های مشابه را پیدا کنیم.</p><div className="form-grid"><label>شهر و محله<div className="input-wrap"><MapPin size={17} /><input value={neighborhood} onChange={(event) => setNeighborhood(event.target.value)} /></div></label><label>متراژ (متر)<div className="input-wrap"><Home size={17} /><input value={area} onChange={(event) => setArea(event.target.value)} inputMode="numeric" /></div></label><label>سن بنا<div className="input-wrap"><Building2 size={17} /><select defaultValue="نوساز"><option>نوساز</option><option>۱ تا ۵ سال</option><option>۵ تا ۱۰ سال</option><option>بیش از ۱۰ سال</option></select><ChevronDown size={15} /></div></label><label>نوع معامله<div className="segmented"><button className="selected">فروش</button><button>رهن و اجاره</button></div></label></div><button className="estimate-button" onClick={runEstimate} disabled={isSubmitting}><Sparkles size={18} /> {isSubmitting ? "در حال تحلیل..." : "محاسبه ارزش ملک"} <ChevronLeft size={17} /></button><p className="form-note">داده‌ها از پایگاه معاملات قیمت‌بان خوانده می‌شوند</p></section>
          <section className="panel estimate-panel"><div className="panel-heading"><div><span className="section-kicker">آخرین تحلیل</span><h2>برآورد قیمت پیشنهادی</h2></div><button className="more-button" aria-label="گزینه‌های بیشتر"><MoreHorizontal size={19} /></button></div><div className="estimate-value"><span>{dashboard?.latest_valuation ? formatNumber(dashboard.latest_valuation.price_mid) : "—"}</span><small>تومان</small></div><div className="estimate-range"><span>بازه اطمینان</span><b>{dashboard?.latest_valuation ? `${formatPrice(dashboard.latest_valuation.price_low)} تا ${formatPrice(dashboard.latest_valuation.price_high)}` : "هنوز تحلیلی ثبت نشده"}</b></div><div className="confidence"><div className="confidence-head"><span>اطمینان مدل</span><b>{dashboard?.latest_valuation ? formatNumber(dashboard.latest_valuation.confidence * 100) : "—"}٪</b></div><div className="confidence-bar"><i style={{ width: `${(dashboard?.latest_valuation?.confidence ?? 0) * 100}%` }} /></div></div><div className="explanation"><div className="explanation-icon"><Sparkles size={17} /></div><p><b>چرا این قیمت؟</b><br />متراژ و موقعیت محله بیشترین اثر را در تحلیل ذخیره‌شده داشته‌اند.</p><ChevronLeft size={17} /></div></section>
        </div>

        <section className="panel comparable-panel"><div className="panel-heading"><div><span className="section-kicker">پیشنهاد هوشمند</span><h2>فایل‌های مشابه نزدیک</h2></div><button className="text-button">مشاهده همه <ChevronLeft size={16} /></button></div><div className="table-head"><span>مشخصات فایل</span><span>قیمت کل</span><span>فاصله</span><span>شباهت</span><span /></div>{dashboard?.comparables.length ? dashboard.comparables.map((item, index) => <div className="comparable-row" key={item.id}><div className="property"><span className={`property-thumb ${["sage", "blue", "sand"][index % 3]}`}><Building2 size={20} /></span><span><b>{item.title}</b><small>{formatNumber(item.area_sqm)} متر · سال {formatNumber(item.year_built)} · طبقه {formatNumber(item.floor)}</small></span></div><b className="price">{formatPrice(item.price)}</b><span className="distance"><MapPin size={14} />اطراف ملک</span><div className="score"><i style={{ width: `${item.similarity * 100}%` }} /><b>{formatNumber(item.similarity * 100)}٪</b></div><button className="row-button" aria-label={`مشاهده ${item.title}`}><ChevronLeft size={17} /></button></div>) : <p className="empty-state">{dashboard ? "هنوز فایل مشابهی ثبت نشده است" : "در حال دریافت فایل‌های مشابه..."}</p>}</section>
        <footer><span>قیمت‌بان · تصمیم‌های بهتر با داده‌های شفاف</span><span>آخرین به‌روزرسانی داده‌ها: ۱۰ دقیقه پیش</span></footer>
      </section>
    </main>
  );
}

function StatCard({ label, value, suffix, change, icon: Icon }: { label: string; value: string; suffix: string; change: string; icon: typeof Sparkles }) {
  return <div className="stat-card"><div className="stat-top"><span className="stat-icon"><Icon size={17} /></span><span className="stat-change">↗ {change}</span></div><p>{label}</p><strong>{value}<small>{suffix}</small></strong></div>;
}
