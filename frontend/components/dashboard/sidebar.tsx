import Link from "next/link";

export function Sidebar({ active = "dashboard" }: { active?: "dashboard" | "valuation" }) {
  return (
    <aside className="sidebar">
      <Link className="sidebarBrand" href="/" aria-label="قیمت‌بان">
        <span className="brandIcon">ق</span>
        <span><strong>قیمت‌بان</strong><small>تصمیم روشن برای ملک</small></span>
      </Link>
      <nav className="sideNav" aria-label="ناوبری پنل">
        <span className="sideLabel">پنل اصلی</span>
        <Link className={active === "dashboard" ? "sideLink active" : "sideLink"} href="/"><span>⌂</span> نمای کلی</Link>
        <Link className={active === "valuation" ? "sideLink active" : "sideLink"} href="/valuation"><span>⌁</span> ارزش‌گذاری جدید</Link>
        <Link className="sideLink" href="/#history"><span>◷</span> تاریخچه تحلیل‌ها</Link>
        <span className="sideLabel sideLabelSpaced">منابع</span>
        <Link className="sideLink" href="/#how"><span>◌</span> روش تحلیل</Link>
      </nav>
      <div className="sidebarBottom">
        <div className="supportCard"><span>?</span><div><strong>راهنمای قیمت‌بان</strong><small>با اطمینان تصمیم بگیرید</small></div></div>
        <div className="profile"><span>م</span><div><strong>مدیر دفتر</strong><small>حساب سازمانی</small></div><b>•••</b></div>
      </div>
    </aside>
  );
}
