"use client";

import type { FormEvent } from "react";
import { useMemo, useState } from "react";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import { Card } from "../ui/card";
import { Progress } from "../ui/progress";

type NumericField = "area_sqm" | "year_built" | "floor" | "total_floors" | "rooms" | "light_score" | "view_score" | "access_score";
type Valuation = { price_low: number; price_mid: number; price_high: number; confidence_level: number; model_version: string; feature_contributions: Record<string, number>; comparables: Array<{ id: string; similarity: number }> };

type FormState = { area_sqm: number; year_built: number; floor: number; total_floors: number; rooms: number; has_parking: boolean; has_elevator: boolean; has_storage: boolean; renovated: boolean; light_score: number; view_score: number; access_score: number };

const labels: Record<string, string> = { area_sqm: "متراژ", year_built: "سال ساخت", floor: "طبقه", total_floors: "تعداد طبقات", rooms: "تعداد خواب", has_parking: "پارکینگ", has_elevator: "آسانسور", has_storage: "انباری", renovated: "بازسازی", light_score: "نورگیری", view_score: "چشم‌انداز", access_score: "دسترسی" };
const initialForm: FormState = { area_sqm: 92, year_built: 1397, floor: 3, total_floors: 6, rooms: 2, has_parking: true, has_elevator: true, has_storage: true, renovated: false, light_score: 4, view_score: 3, access_score: 4 };
const money = (value: number) => new Intl.NumberFormat("fa-IR", { notation: "compact", maximumFractionDigits: 1 }).format(value) + " تومان";
const percent = (value: number) => new Intl.NumberFormat("fa-IR", { style: "percent", maximumFractionDigits: 0 }).format(value);

export function ValuationWorkspace({ compact = false }: { compact?: boolean }) {
  const [form, setForm] = useState<FormState>(initialForm);
  const [result, setResult] = useState<Valuation | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const contributions = useMemo(() => Object.entries(result?.feature_contributions ?? {}).sort((a, b) => Math.abs(b[1]) - Math.abs(a[1])).slice(0, 6), [result]);
  const maxContribution = Math.max(1, ...contributions.map(([, value]) => Math.abs(value)));

  async function submit(event: FormEvent) {
    event.preventDefault(); setLoading(true); setError("");
    try {
      const response = await fetch("/api/valuations", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(form) });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.detail ?? "ارزش‌گذاری انجام نشد");
      setResult(payload);
    } catch (reason) { setError(reason instanceof Error ? reason.message : "ارتباط با سرویس برقرار نشد"); }
    finally { setLoading(false); }
  }

  function setNumber(key: NumericField, value: string) { setForm((current) => ({ ...current, [key]: Number(value) })); }

  return <div className={`valuationWorkspace ${compact ? "valuationWorkspaceCompact" : ""}`}>
    <Card className="valuationFormCard">
      <div className="cardHeading"><div className="stepNumber">۱</div><div><span className="sectionKicker">ورودی تحلیل</span><h2>مشخصات ملک</h2><p>اطلاعات دقیق‌تر، تحلیل قابل اتکاتر</p></div></div>
      <form onSubmit={submit}>
        <div className="fieldGrid">
          {(["area_sqm", "year_built", "floor", "total_floors", "rooms"] as NumericField[]).map((key) => <label key={key}>{labels[key]}<input type="number" min={key === "year_built" ? 1300 : 0} value={form[key]} onChange={(event) => setNumber(key, event.target.value)} /></label>)}
        </div>
        <div className="scoreBox"><div className="scoreBoxHeader"><span>شاخص‌های کیفی</span><small>از ۱ تا ۵</small></div>{(["light_score", "view_score", "access_score"] as NumericField[]).map((key) => <label className="scoreRow" key={key}><span>{labels[key]}</span><input type="range" min="1" max="5" value={form[key]} onChange={(event) => setNumber(key, event.target.value)} /><b>{form[key]}</b></label>)}</div>
        <div className="toggleGrid">{(["has_parking", "has_elevator", "has_storage", "renovated"] as const).map((key) => <label key={key}><input type="checkbox" checked={form[key]} onChange={(event) => setForm((current) => ({ ...current, [key]: event.target.checked }))} /><span />{labels[key]}</label>)}</div>
        <Button className="submitButton" size="lg" disabled={loading}>{loading ? "در حال تحلیل…" : "تحلیل ارزش ملک"}<span>←</span></Button>
        {error && <p className="formError" role="alert">{error}</p>}
      </form>
    </Card>
    <Card className={`valuationResultCard ${result ? "hasResult" : ""}`} aria-live="polite">
      {!result ? <div className="emptyResult"><div className="emptyChart"><i /><i /><i /><i /></div><span className="sectionKicker">نتیجهٔ تحلیل</span><h2>تحلیل شما اینجا شکل می‌گیرد</h2><p>مشخصات ملک را وارد کنید تا بازهٔ قیمت و منطق پشت آن را ببینید.</p><div className="skeletonLines"><i /><i /><i /></div></div> : <>
        <div className="resultTop"><div><span className="sectionKicker">برآورد مدل</span><h2>{money(result.price_mid)}</h2><p>قیمت میانی پیشنهادی</p></div><Badge tone="success">اطمینان {percent(result.confidence_level)}</Badge></div>
        <div className="priceRange"><span className="rangeTrack" /><span className="rangeDot" /><div><strong>{money(result.price_low)}</strong><small>کف بازه</small></div><div><strong>{money(result.price_high)}</strong><small>سقف بازه</small></div></div>
        <div className="analysisSection"><div className="subsectionHeading"><h3>چه چیزی قیمت را ساخته؟</h3><span>سهم ویژگی‌ها</span></div>{contributions.map(([key, value]) => <div className="factorRow" key={key}><span>{labels[key] ?? key}</span><Progress value={Math.abs(value) / maxContribution * 100} tone={value < 0 ? "coral" : "turquoise"} /><strong className={value < 0 ? "negativeValue" : ""}>{value >= 0 ? "+" : "−"}{money(Math.abs(value))}</strong></div>)}</div>
        <div className="comparablesSection"><div className="subsectionHeading"><h3>فایل‌های مشابه</h3><span>بر اساس شباهت برداری</span></div>{result.comparables.slice(0, 3).map((item, index) => <div className="comparableRow" key={item.id}><span className="comparableIndex">{new Intl.NumberFormat("fa-IR").format(index + 1)}</span><code>{item.id.slice(0, 12)}</code><b>{percent(item.similarity)} شباهت</b></div>)}</div>
        <small className="modelVersion">نسخه مدل: {result.model_version}</small>
      </>}
    </Card>
  </div>;
}
