import { clsx } from "clsx";
import type { LucideIcon } from "lucide-react";

interface Props {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  trend?: "up" | "down" | "neutral";
  color?: "brand" | "green" | "amber" | "red";
}

const COLOR_MAP = {
  brand:  "bg-brand-600/20 text-brand-400",
  green:  "bg-green-900/30 text-green-400",
  amber:  "bg-amber-900/30 text-amber-400",
  red:    "bg-red-900/30 text-red-400",
};

export default function StatCard({ title, value, subtitle, icon: Icon, color = "brand" }: Props) {
  return (
    <div className="card flex items-center gap-4">
      <div className={clsx("p-3 rounded-xl flex-shrink-0", COLOR_MAP[color])}>
        <Icon size={20} />
      </div>
      <div className="min-w-0">
        <p className="text-xs text-slate-500 mb-0.5">{title}</p>
        <p className="text-2xl font-bold text-slate-100">{value}</p>
        {subtitle && <p className="text-xs text-slate-500 mt-0.5 truncate">{subtitle}</p>}
      </div>
    </div>
  );
}
