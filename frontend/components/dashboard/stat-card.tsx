import { Card } from "../ui/card";

type StatCardProps = { label: string; value: string; detail: string; icon: string; tone?: "turquoise" | "amber" | "coral" };

export function StatCard({ label, value, detail, icon, tone = "turquoise" }: StatCardProps) {
  return <Card className="statCard"><div className={`statIcon statIcon-${tone}`}>{icon}</div><div className="statCopy"><span>{label}</span><strong>{value}</strong><small>{detail}</small></div></Card>;
}
