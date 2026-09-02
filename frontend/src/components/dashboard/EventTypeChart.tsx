import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Cell,
} from "recharts";

const COLORS = ["#0ea5e9","#8b5cf6","#f59e0b","#ef4444","#22c55e","#ec4899","#06b6d4","#f97316"];

interface Props {
  data: Record<string, number>;
}

export default function EventTypeChart({ data }: Props) {
  const chartData = Object.entries(data)
    .map(([name, value]) => ({ name: name.replace(/_/g, " "), value }))
    .sort((a, b) => b.value - a.value);

  return (
    <div className="card">
      <h3 className="text-sm font-semibold text-slate-300 mb-4">Events by Type — 24h</h3>
      <ResponsiveContainer width="100%" height={180}>
        <BarChart data={chartData} margin={{ top: 4, right: 8, left: -20, bottom: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
          <XAxis
            dataKey="name"
            tick={{ fontSize: 9, fill: "#64748b" }}
            angle={-30}
            textAnchor="end"
            tickLine={false}
          />
          <YAxis tick={{ fontSize: 10, fill: "#64748b" }} tickLine={false} axisLine={false} />
          <Tooltip
            contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 8 }}
            labelStyle={{ color: "#94a3b8", fontSize: 11 }}
            itemStyle={{ fontSize: 11 }}
          />
          <Bar dataKey="value" name="Count" radius={[4, 4, 0, 0]}>
            {chartData.map((_, i) => (
              <Cell key={i} fill={COLORS[i % COLORS.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
