import type { HTMLAttributes } from "react";

type BadgeProps = HTMLAttributes<HTMLSpanElement> & { tone?: "success" | "neutral" | "warning" };

export function Badge({ className = "", tone = "neutral", ...props }: BadgeProps) {
  return <span className={`uiBadge uiBadge-${tone} ${className}`.trim()} {...props} />;
}
