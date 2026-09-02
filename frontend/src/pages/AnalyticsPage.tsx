import { useEffect, useState } from "react";
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Legend, Cell,
} from "recharts";
import { format, parseISO } from "date-fns";
import { analyticsApi } from "@/api/endpoints";
import LoadingSpinner from "@/components/common/LoadingSpinner";

const COLORS = ["#0ea5e9","#8b5cf6","#f59e0b","#ef4444","#22c55e","#ec4899","#06b6d4","#f97316"];

export default function AnalyticsPage() {
  const [timeline,  setTimeline]  = useState<{ hour: string; event_type: string; count: number }[]>([]);
  const [heatmap,   setHeatmap]   = useState<{ camera_id: string; total: number }[]>([]);
  const [loading,   setLoading]   = useState(true);
  const [hours,     setHours]     = useState(24);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const [tl, hm] = await Promise.all([
          analyticsApi.timeline(undefined, hours),
          analyticsApi.heatmap(hours),
        ]);
        setTimeline(tl);
        setHeatmap(hm);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [hours]);

  // Pivot timeline into recharts format: [{hour, type1: n, type2: n, ...}]
  const eventTypes = [...new Set(timeline.map((d) => d.event_type))];
  const hourMap: Record<string, Record<string, number>> = {};
  for (const d of timeline) {
    if (!hourMap[d.hour]) hourMap[d.hour] = {};
    hourMap[d.hour][d.event_type] = d.count;
  }
  const lineData = Object.entries(hourMap)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([hour, counts]) => ({
      label: format(parseISO(hour), "HH:mm"),
      ...counts,
    }));

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-100">Analytics</h1>
          <p className="text-sm text-slate-500">Surveillance Intelligence Report</p>
        </div>
        <select
          className="input w-auto text-xs"
          value={hours}
          onChange={(e) => setHours(Number(e.target.value))}
        >
          <option value={6}>Last 6h</option>
          <option value={24}>Last 24h</option>
          <option value={48}>Last 48h</option>
          <option value={168}>Last 7d</option>
        </select>
      </div>

      {loading ? <LoadingSpinner /> : (
        <>
          {/* Multi-line event type trend */}
          <div className="card">
            <h3 className="text-sm font-semibold text-slate-300 mb-4">Event Types Over Time</h3>
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={lineData} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="label" tick={{ fontSize: 10, fill: "#64748b" }} tickLine={false} />
                <YAxis tick={{ fontSize: 10, fill: "#64748b" }} tickLine={false} axisLine={false} />
                <Tooltip
                  contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 8 }}
                  labelStyle={{ color: "#94a3b8", fontSize: 11 }}
                  itemStyle={{ fontSize: 11 }}
                />
                <Legend wrapperStyle={{ fontSize: 10, color: "#94a3b8" }} />
                {eventTypes.map((type, i) => (
                  <Line
                    key={type}
                    type="monotone"
                    dataKey={type}
                    name={type.replace(/_/g, " ")}
                    stroke={COLORS[i % COLORS.length]}
                    strokeWidth={2}
                    dot={false}
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Camera heatmap bar chart */}
          <div className="card">
            <h3 className="text-sm font-semibold text-slate-300 mb-4">Alert Volume by Camera</h3>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart
                data={heatmap}
                layout="vertical"
                margin={{ top: 4, right: 16, left: 60, bottom: 0 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis type="number" tick={{ fontSize: 10, fill: "#64748b" }} tickLine={false} />
                <YAxis dataKey="camera_id" type="category" tick={{ fontSize: 10, fill: "#64748b" }} tickLine={false} width={56} />
                <Tooltip
                  contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 8 }}
                  itemStyle={{ fontSize: 11 }}
                />
                <Bar dataKey="total" name="Alerts" radius={[0, 4, 4, 0]}>
                  {heatmap.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </>
      )}
    </div>
  );
}
