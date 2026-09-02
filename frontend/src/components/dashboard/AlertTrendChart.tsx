import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer,
} from "recharts";
import { format, parseISO } from "date-fns";

interface Props {
  data: Array<{ hour: string; count: number }>;
}

export default function AlertTrendChart({ data }: Props) {
  const formatted = data.map((d) => ({
    ...d,
    label: format(parseISO(d.hour), "HH:mm"),
  }));

  return (
    <div className="card">
      <h3 className="text-sm font-semibold text-slate-300 mb-4">Alert Trend — Last 24h</h3>
      <ResponsiveContainer width="100%" height={180}>
        <AreaChart data={formatted} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
          <defs>
            <linearGradient id="alertGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%"  stopColor="#0ea5e9" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#0ea5e9" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
          <XAxis dataKey="label" tick={{ fontSize: 10, fill: "#64748b" }} tickLine={false} />
          <YAxis tick={{ fontSize: 10, fill: "#64748b" }} tickLine={false} axisLine={false} />
          <Tooltip
            contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 8 }}
            labelStyle={{ color: "#94a3b8", fontSize: 11 }}
            itemStyle={{ color: "#38bdf8", fontSize: 11 }}
          />
          <Area
            type="monotone"
            dataKey="count"
            stroke="#0ea5e9"
            strokeWidth={2}
            fill="url(#alertGrad)"
            name="Alerts"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
