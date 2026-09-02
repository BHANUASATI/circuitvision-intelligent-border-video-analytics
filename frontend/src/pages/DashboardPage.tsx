import { useEffect, useState } from "react";
import { Camera, Bell, AlertTriangle, Activity, RefreshCw } from "lucide-react";
import { analyticsApi } from "@/api/endpoints";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { fetchCounts } from "@/store/slices/alertsSlice";
import { fetchCameras } from "@/store/slices/camerasSlice";
import StatCard from "@/components/dashboard/StatCard";
import AlertTrendChart from "@/components/dashboard/AlertTrendChart";
import EventTypeChart from "@/components/dashboard/EventTypeChart";
import LoadingSpinner from "@/components/common/LoadingSpinner";
import type { DashboardSummary } from "@/types";

export default function DashboardPage() {
  const dispatch  = useAppDispatch();
  const cameras   = useAppSelector((s) => s.cameras.items);
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const [s] = await Promise.all([
        analyticsApi.dashboard(),
        dispatch(fetchCameras()),
        dispatch(fetchCounts()),
      ]);
      setSummary(s);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  if (loading && !summary) return <LoadingSpinner />;

  const active = cameras.filter((c) => c.is_streaming).length;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-100">Command & Control</h1>
          <p className="text-sm text-slate-500">Border Surveillance Overview</p>
        </div>
        <button onClick={load} className="btn-ghost flex items-center gap-2 text-sm">
          <RefreshCw size={15} className={loading ? "animate-spin" : ""} />
          Refresh
        </button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Cameras"
          value={summary?.cameras.total ?? cameras.length}
          subtitle={`${active} streaming`}
          icon={Camera}
          color="brand"
        />
        <StatCard
          title="Active Streams"
          value={summary?.cameras.active_streams ?? active}
          subtitle="Live AI analytics"
          icon={Activity}
          color="green"
        />
        <StatCard
          title="Alerts — 24h"
          value={summary?.alerts.last_24h ?? 0}
          subtitle={`${summary?.alerts.unacknowledged ?? 0} unacknowledged`}
          icon={Bell}
          color="amber"
        />
        <StatCard
          title="Open Incidents"
          value={summary?.incidents.open ?? 0}
          subtitle="Requires attention"
          icon={AlertTriangle}
          color="red"
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <AlertTrendChart data={summary?.alerts.hourly_trend ?? []} />
        <EventTypeChart data={summary?.alerts.by_event_type ?? {}} />
      </div>

      {/* Severity breakdown */}
      {summary && (
        <div className="card">
          <h3 className="text-sm font-semibold text-slate-300 mb-4">Alert Severity Breakdown — 24h</h3>
          <div className="grid grid-cols-4 gap-3">
            {(["LOW", "MEDIUM", "HIGH", "CRITICAL"] as const).map((sev) => (
              <div key={sev} className="text-center">
                <div className={`text-2xl font-bold mb-1 ${
                  sev === "LOW"      ? "text-green-400"  :
                  sev === "MEDIUM"   ? "text-amber-400"  :
                  sev === "HIGH"     ? "text-red-400"    :
                  "text-red-300"
                }`}>
                  {summary.alerts.by_severity[sev] ?? 0}
                </div>
                <p className="text-xs text-slate-500">{sev}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
