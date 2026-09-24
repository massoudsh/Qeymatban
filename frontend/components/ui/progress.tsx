type ProgressProps = { value: number; tone?: "turquoise" | "amber" | "coral" };

export function Progress({ value, tone = "turquoise" }: ProgressProps) {
  return <span className="uiProgress"><span className={`uiProgressFill uiProgress-${tone}`} style={{ width: `${Math.min(100, Math.max(0, value))}%` }} /></span>;
}
