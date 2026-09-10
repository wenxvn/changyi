import type { ReactNode } from "react";

interface StatusPillProps {
  children: ReactNode;
  tone?: "neutral" | "success" | "warning" | "danger";
}

export function StatusPill({ children, tone = "neutral" }: StatusPillProps) {
  return <span className={`status-pill status-pill--${tone}`}>{children}</span>;
}
