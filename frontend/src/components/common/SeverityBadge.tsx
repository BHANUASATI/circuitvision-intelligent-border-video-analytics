import { clsx } from "clsx";
import type { AlertSeverity } from "@/types";

const MAP: Record<AlertSeverity, string> = {
  LOW:      "severity-low",
  MEDIUM:   "severity-medium",
  HIGH:     "severity-high",
  CRITICAL: "severity-critical",
};

export default function SeverityBadge({ severity }: { severity: AlertSeverity }) {
  return (
    <span className={clsx("badge", MAP[severity])}>{severity}</span>
  );
}
