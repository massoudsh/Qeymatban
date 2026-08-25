"use client";

import { FormEvent, useMemo, useState } from "react";

type NumericField =
  | "area_sqm"
  | "year_built"
  | "floor"
  | "total_floors"
  | "rooms"
  | "light_score"
  | "view_score"
  | "access_score";

type Valuation = {
  price_low: number;
  price_mid: number;
  price_high: number;
  confidence_level: number;
  model_version: string;
  feature_contributions: Record<string, number>;
  comparables: Array<{ id: string; similarity: number }>;
};

const labels: Record<string, string> = {
  area_sqm: "متراژ",
  year_built: "سال ساخت",
  floor: "طبقه",
  total_floors: "تعداد طبقات",
  rooms: "تعداد خواب",
  has_parking: "پارکینگ",
  has_elevator: "آسانسور",
  has_storage: "انباری",
  renovated: "بازسازی",
  light_score: "نورگیری",
  view_score: "چشم‌انداز",
  access_score: "دسترسی",
};

const initialForm = {
  area_sqm: 92,
  year_built: 1397,
  floor: 3,
  total_floors: 6,
  rooms: 2,
  has_parking: true,
  has_elevator: true,
  has_storage: true,
  renovated: false,
  light_score: 4,
  view_score: 3,
  access_score: 4,
};

const money = (value: number) =>
  new Intl.NumberFormat("fa-IR", { notation: "compact", maximumFractionDigits: 1 }).format(value) + " تومان";

export default function Dashboard() {
  const [form, setForm] = useState(initialForm);
  const [result, setResult] = useState<Valuation | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const contributions = useMemo(
    () => Object.entries(result?.feature_contributions ?? {}).sort((a, b) => Math.abs(b[1]) - Math.abs(a[1])).slice(0, 6),
    [result],
  );
  const maxContribution = Math.max(1, ...contributions.map(([, value]) => Math.abs(value)));

  async function submit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      const response = await fetch("/api/valuations", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.detail ?? "ارزش‌گذاری انجام نشد");
      setResult(payload);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "ارتباط با سرویس برقرار نشد");
    } finally {
      setLoading(false);
    }
  }

  function setNumber(key: NumericField, value: string) {
    setForm((current) => ({ ...current, [key]: Number(value) }));
  }

  return (
    <main>
      <header className="topbar">
        <a className="brand" href="#top" aria-label="قیمت‌بان">
          <span className="brandMark">ق</span>
          <span>قیمت‌بان<small>تصمیم روشن برای ملک</small></span>
        </a>
        <nav aria-label="ناوبری اصلی">
          <a className="active" href="#valuation">ارزش‌گذاری</a>
          <a href="#how">روش تحلیل</a>
        </nav>
        <span className="status"><i /> موتور تحلیل</span>
      </header>

      <section className="hero" id="top">
        <div>
          <span className="eyebrow">تحلیل داده‌محور بازار مسکن</span>
          <h1>قیمت ملک، فقط یک عدد نیست.<br /><strong>یک توضیح قابل دفاع است.</strong></h1>
          <p>بازه‌ی واقعی قیمت را ببینید، فایل‌های مشابه را مقایسه کنید و بفهمید هر ویژگی چقدر بر ارزش ملک اثر گذاشته است.</p>
        </div>
        <div className="trustMetric"><b>۸۰٪</b><span>بازه اطمینان مدل<small>به‌جای ادعای قیمت قطعی</small></span></div>
      </section>

      <section className="workspace" id="valuation">
        <form className="panel formPanel" onSubmit={submit}>
          <div className="panelTitle"><span>۱</span><div><h2>مشخصات ملک</h2><p>اطلاعات دقیق‌تر، تحلیل قابل اتکاتر</p></div></div>
          <div className="fields">
            <label>متراژ (متر مربع)<input type="number" min="1" value={form.area_sqm} onChange={(e) => setNumber("area_sqm", e.target.value)} /></label>
            <label>سال ساخت<input type="number" min="1300" max="1500" value={form.year_built} onChange={(e) => setNumber("year_built", e.target.value)} /></label>
            <label>طبقه<input type="number" value={form.floor} onChange={(e) => setNumber("floor", e.target.value)} /></label>
            <label>تعداد طبقات<input type="number" min="1" value={form.total_floors} onChange={(e) => setNumber("total_floors", e.target.value)} /></label>
            <label>تعداد خواب<input type="number" min="0" value={form.rooms} onChange={(e) => setNumber("rooms", e.target.value)} /></label>
          </div>
          <div className="scoreGrid">
            {(["light_score", "view_score", "access_score"] as const).map((key) => (
              <label key={key}>{labels[key]}<input type="range" min="1" max="5" value={form[key]} onChange={(e) => setNumber(key, e.target.value)} /><b>{form[key]} از ۵</b></label>
            ))}
          </div>
          <div className="toggles">
            {(["has_parking", "has_elevator", "has_storage", "renovated"] as const).map((key) => (
              <label key={key}><input type="checkbox" checked={form[key]} onChange={(e) => setForm((current) => ({ ...current, [key]: e.target.checked }))} /><span />{labels[key]}</label>
            ))}
          </div>
          <button className="primary" disabled={loading}>{loading ? "در حال تحلیل…" : "تحلیل ارزش ملک"}<span>←</span></button>
          {error && <p className="error" role="alert">{error}</p>}
        </form>

        <section className={`panel resultPanel ${result ? "hasResult" : ""}`} aria-live="polite">
          {!result ? (
            <div className="emptyState">
              <div className="signal"><span /><span /><span /><span /></div>
              <h2>تحلیل شما اینجا شکل می‌گیرد</h2>
              <p>مشخصات ملک را وارد کنید تا موتور قیمت‌بان بازه قیمت و منطق پشت آن را نمایش دهد.</p>
              <div className="previewRows"><i /><i /><i /></div>
            </div>
          ) : (
            <>
              <div className="resultHeader"><div><span className="eyebrow">برآورد مدل</span><h2>{money(result.price_mid)}</h2><p>قیمت میانی پیشنهادی</p></div><span className="confidence">اطمینان {new Intl.NumberFormat("fa-IR", { style: "percent" }).format(result.confidence_level)}</span></div>
              <div className="range"><span style={{ width: "72%" }} /><i /><div><b>{money(result.price_low)}</b><small>کف بازه</small></div><div><b>{money(result.price_high)}</b><small>سقف بازه</small></div></div>
              <div className="analysisBlock"><h3>چه چیزی قیمت را ساخته؟</h3>{contributions.map(([key, value]) => <div className="factor" key={key}><span>{labels[key] ?? key}</span><i><b className={value < 0 ? "negative" : ""} style={{ width: `${Math.max(4, Math.abs(value) / maxContribution * 100)}%` }} /></i><strong className={value < 0 ? "negativeText" : ""}>{value >= 0 ? "+" : "−"}{money(Math.abs(value))}</strong></div>)}</div>
              <div className="comps"><h3>فایل‌های مشابه</h3>{result.comparables.slice(0, 3).map((item, index) => <div key={item.id}><span>{new Intl.NumberFormat("fa-IR").format(index + 1)}</span><code>{item.id.slice(0, 12)}</code><b>{new Intl.NumberFormat("fa-IR", { style: "percent" }).format(item.similarity)} شباهت</b></div>)}</div>
              <small className="modelVersion">نسخه مدل: {result.model_version}</small>
            </>
          )}
        </section>
      </section>

      <section className="how" id="how">
        <span className="eyebrow">چرا قیمت‌بان؟</span><h2>از حدس بازار تا تصمیم مستند</h2>
        <div>{[["۰۱", "بازه، نه عدد قطعی", "عدم‌قطعیت بازار را پنهان نمی‌کنیم."], ["۰۲", "مقایسه واقعی", "نزدیک‌ترین معاملات را مبنای تحلیل می‌کنیم."], ["۰۳", "توضیح شفاف", "اثر نور، طبقه، سن و امکانات قابل مشاهده است."]].map(([n, title, text]) => <article key={n}><b>{n}</b><h3>{title}</h3><p>{text}</p></article>)}</div>
      </section>
      <footer><span>قیمت‌بان</span><p>ابزار تصمیم‌یار است، نه جایگزین ارزیابی کارشناس.</p></footer>
    </main>
  );
}
