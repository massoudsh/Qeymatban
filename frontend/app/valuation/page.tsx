import { Sidebar } from "../../components/dashboard/sidebar";
import { ValuationWorkspace } from "../../components/dashboard/valuation-workspace";

export default function ValuationPage() {
  return <div className="appShell"><Sidebar active="valuation" /><main className="mainContent"><header className="pageHeader valuationPageHeader"><div><span className="sectionKicker">موتور ارزش‌گذاری</span><h1>ارزش‌گذاری جدید</h1><p>ویژگی‌های ملک را وارد کنید تا برآورد توضیح‌پذیر دریافت کنید.</p></div></header><ValuationWorkspace /></main></div>;
}
